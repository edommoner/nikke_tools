// Metal transport only. Numeric/state/event logic lives in shared Slang sources.
import Foundation
import Metal
import Darwin

// The encoder dispatches exactly one independent program per threadgroup.
let portableThreadsPerThreadgroup = 1

struct ProbeError: Error, CustomStringConvertible {
    let description: String
    init(_ message: String) { description = message }
}

// Serialize pipeline creation across worker processes. A concurrent cold
// compile of the same large kernel can stall in the Metal compiler service.
// Release before buffer encoding/dispatch; GPU work is not held by this lock.
func compilePipeline(device: MTLDevice, source: String, entry: String, lockURL: URL, residentStride: Int = 0) throws
    -> (pipeline: MTLComputePipelineState, librarySeconds: Double, pipelineSeconds: Double, lockWaitSeconds: Double) {
    let descriptor = open(lockURL.path, O_CREAT | O_RDWR, 0o600)
    guard descriptor >= 0 else { throw ProbeError("Cannot open Metal pipeline lock") }
    defer { close(descriptor) }
    FileHandle.standardError.write(Data("portable_stage=pipeline_lock\n".utf8))
    let lockStart = Date().timeIntervalSinceReferenceDate
    while flock(descriptor, LOCK_EX) != 0 {
        if errno != EINTR { throw ProbeError("Cannot acquire Metal pipeline lock") }
    }
    let lockWaitSeconds = Date().timeIntervalSinceReferenceDate - lockStart
    defer { flock(descriptor, LOCK_UN) }
    let options = MTLCompileOptions()
    options.mathMode = .safe
    FileHandle.standardError.write(Data("portable_stage=library_compile\n".utf8))
    let libraryStart = Date().timeIntervalSinceReferenceDate
    let library = try device.makeLibrary(source: source, options: options)
    let librarySeconds = Date().timeIntervalSinceReferenceDate - libraryStart
    guard let function = library.makeFunction(name: entry) else { throw ProbeError("Missing \(entry) entry") }
    FileHandle.standardError.write(Data("portable_stage=pipeline_compile\n".utf8))
    let pipelineStart = Date().timeIntervalSinceReferenceDate
    let pipelineDescriptor = MTLComputePipelineDescriptor()
    pipelineDescriptor.computeFunction = function
    pipelineDescriptor.maxTotalThreadsPerThreadgroup = portableThreadsPerThreadgroup
    var reflection: MTLComputePipelineReflection?
    let pipelineOptions: MTLPipelineOption = residentStride > 0 ? [.argumentInfo, .bufferTypeInfo] : []
    let pipeline = try device.makeComputePipelineState(descriptor: pipelineDescriptor, options: pipelineOptions, reflection: &reflection)
    if residentStride > 0 {
        guard let state = reflection?.arguments.first(where: { $0.type == .buffer && $0.index == 2 }),
              state.bufferDataSize == residentStride else {
            throw ProbeError("Resident Runtime physical Metal layout differs from Slang reflection")
        }
    }
    let pipelineSeconds = Date().timeIntervalSinceReferenceDate - pipelineStart
    return (pipeline, librarySeconds, pipelineSeconds, lockWaitSeconds)
}

func run() throws {
    guard [4, 7, 8].contains(CommandLine.arguments.count) else { throw ProbeError("Expected: shader.metal input.bin output.bin [entry inputWords outputWords]") }
    let entry = CommandLine.arguments.count >= 7 ? CommandLine.arguments[4] : "portableProbe"
    let inputWords = CommandLine.arguments.count >= 7 ? Int(CommandLine.arguments[5]) ?? 0 : 97
    let outputWords = CommandLine.arguments.count >= 7 ? Int(CommandLine.arguments[6]) ?? 0 : 7
    let residentStride = CommandLine.arguments.count == 8 ? Int(CommandLine.arguments[7]) ?? 0 : 0
    guard CommandLine.arguments.count != 8 || (residentStride > 0 && residentStride <= 1048576 && residentStride % 8 == 0) else { throw ProbeError("Invalid resident stride") }
    guard inputWords > 0 && inputWords <= 131072 && outputWords > 0 && (outputWords <= 524288 || outputWords == 655360 || outputWords == 786432) else { throw ProbeError("Invalid wire layout") }
    guard let device = MTLCreateSystemDefaultDevice() else { throw ProbeError("No Metal device") }
    let sequence = CommandLine.arguments[3] == "--batches"
    let paths: [[String: String]]
    if sequence {
        let data = try Data(contentsOf: URL(fileURLWithPath: CommandLine.arguments[2]))
        paths = try JSONDecoder().decode([[String: String]].self, from: data)
        guard !paths.isEmpty else { throw ProbeError("Empty dispatch sequence") }
    } else { paths = [["input": CommandLine.arguments[2], "output": CommandLine.arguments[3]]] }
    func readInput(_ path: [String: String]) throws -> (Data, Int, Int) {
        guard let name = path["input"], path["output"] != nil else { throw ProbeError("Missing dispatch path") }
        let inputData = try Data(contentsOf: URL(fileURLWithPath: name))
        guard inputData.count >= 4 else { throw ProbeError("Missing input header") }
        let count = inputData.withUnsafeBytes { UInt32(littleEndian: $0.loadUnaligned(as: UInt32.self)) }
        guard count > 0 && count <= 65536 && inputData.count == (1 + Int(count) * inputWords) * 4 else { throw ProbeError("Invalid input dimensions") }
        guard 1 + Int(count) * inputWords <= Int(UInt32.max), Int(count) * outputWords <= Int(UInt32.max) else { throw ProbeError("Wire addressing exceeds uint32") }
        let outputSize = Int(count) * outputWords * 4
        guard inputData.count <= device.maxBufferLength && outputSize <= device.maxBufferLength else { throw ProbeError("Wire buffer exceeds device limit") }
        return (inputData, Int(count), outputSize)
    }
    var maxInput = 0, maxOutput = 0, maxCount = 0
    for path in paths {
        let (data, count, size) = try readInput(path)
        maxInput = max(maxInput, data.count); maxOutput = max(maxOutput, size); maxCount = max(maxCount, count)
    }
    guard let input = device.makeBuffer(length: maxInput, options: .storageModeShared),
          let output = device.makeBuffer(length: maxOutput, options: .storageModeShared),
          let queue = device.makeCommandQueue() else { throw ProbeError("Metal allocation failed") }
    let runtimeBytes = residentStride * maxCount
    guard runtimeBytes <= device.maxBufferLength else { throw ProbeError("Resident buffer exceeds device limit") }
    let runtime: MTLBuffer? = residentStride > 0 ? device.makeBuffer(length: runtimeBytes, options: .storageModePrivate) : nil
    guard residentStride == 0 || runtime != nil else { throw ProbeError("Resident allocation failed") }
    let source = try String(contentsOfFile: CommandLine.arguments[1], encoding: .utf8)
    let shaderURL = URL(fileURLWithPath: CommandLine.arguments[1])
    let lockURL = shaderURL.deletingLastPathComponent().appendingPathComponent("metal-pipeline.lock")
    let compiled = try compilePipeline(device: device, source: source, entry: entry, lockURL: lockURL, residentStride: residentStride)
    let pipeline = compiled.pipeline
    var statuses: [[String: Any]] = []
    for path in paths {
        let (inputData, count, outputSize) = try readInput(path)
        inputData.withUnsafeBytes { bytes in input.contents().copyMemory(from: bytes.baseAddress!, byteCount: bytes.count) }
        output.contents().initializeMemory(as: UInt8.self, repeating: 0, count: outputSize)
        guard let command = queue.makeCommandBuffer(), let encoder = command.makeComputeCommandEncoder() else { throw ProbeError("Metal command creation failed") }
        encoder.setComputePipelineState(pipeline)
        encoder.setBuffer(input, offset: 0, index: 0)
        encoder.setBuffer(output, offset: 0, index: 1)
        if let state = runtime { encoder.setBuffer(state, offset: 0, index: 2) }
        encoder.dispatchThreadgroups(MTLSize(width: Int(count), height: 1, depth: 1), threadsPerThreadgroup: MTLSize(width: portableThreadsPerThreadgroup, height: 1, depth: 1))
        encoder.endEncoding()
        FileHandle.standardError.write(Data("portable_stage=gpu_dispatch\n".utf8))
        command.commit()
        command.waitUntilCompleted()
        guard command.status == .completed else { throw ProbeError(command.error?.localizedDescription ?? "Metal execution failed") }
        try Data(bytes: output.contents(), count: outputSize).write(to: URL(fileURLWithPath: path["output"]!), options: .atomic)
        var status: [String: Any] = ["backend": "metal", "device": device.name, "cases": count,
            "command_status": "completed", "registry_id": String(device.registryID),
            "gpu_seconds": command.gpuEndTime - command.gpuStartTime,
            "configured_max_threads_per_threadgroup": portableThreadsPerThreadgroup,
            "threads_per_threadgroup": portableThreadsPerThreadgroup,
            "pipeline_max_threads_per_threadgroup": pipeline.maxTotalThreadsPerThreadgroup,
            "library_compile_seconds": compiled.librarySeconds, "pipeline_compile_seconds": compiled.pipelineSeconds,
            "pipeline_lock_wait_seconds": compiled.lockWaitSeconds,
            "input_bytes": inputData.count, "output_bytes": outputSize]
        if residentStride > 0 {
            status["runtime_stride_bytes"] = residentStride
            status["runtime_buffer_bytes"] = runtimeBytes
            status["runtime_element_capacity"] = maxCount
            status["runtime_physical_stride_verified"] = true
        }
        statuses.append(status)
    }
    let result: [String: Any] = sequence ? ["batches": statuses, "pipeline_instances": 1, "buffer_allocations": residentStride > 0 ? 3 : 2] : statuses[0]
    print(String(data: try JSONSerialization.data(withJSONObject: result, options: [.sortedKeys]), encoding: .utf8)!)
}

do { try run() }
catch { FileHandle.standardError.write(Data("\(error)\n".utf8)); exit(1) }
