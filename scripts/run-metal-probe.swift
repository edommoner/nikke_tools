// Metal transport only. Numeric/state/event logic lives in shared Slang sources.
import Foundation
import Metal
import Darwin
import CryptoKit

// The encoder dispatches exactly one independent program per threadgroup.
let portableThreadsPerThreadgroup = 1

struct ProbeError: Error, CustomStringConvertible {
    let description: String
    init(_ message: String) { description = message }
}

func sha256(_ data: Data) -> String { SHA256.hash(data: data).map { String(format: "%02x", $0) }.joined() }
func canonicalJSON(_ value: Any) throws -> Data {
    try JSONSerialization.data(withJSONObject: value, options: [.sortedKeys, .withoutEscapingSlashes])
}
struct PipelineCacheRecord: Codable {
    let identity: [String: String]
    let archive_sha256: String
    let archive_bytes: Int
}
struct PipelineCacheRequest {
    let root: URL
    let identity: [String: String]
    let key: String
    let required: Bool
    var archiveURL: URL { root.appendingPathComponent(key + ".metalarc") }
    var recordURL: URL { root.appendingPathComponent(key + ".json") }
    func read() throws -> PipelineCacheRecord? {
        let archiveExists = FileManager.default.fileExists(atPath: archiveURL.path)
        let recordExists = FileManager.default.fileExists(atPath: recordURL.path)
        if !archiveExists && !recordExists {
            if required { throw ProbeError("Required Metal pipeline cache miss: \(key)") }
            return nil
        }
        guard archiveExists && recordExists else { throw ProbeError("Incomplete Metal pipeline cache: \(key)") }
        let record = try JSONDecoder().decode(PipelineCacheRecord.self, from: Data(contentsOf: recordURL))
        let bytes = try Data(contentsOf: archiveURL)
        guard record.identity == identity, record.archive_bytes > 0,
              record.archive_bytes == bytes.count, record.archive_sha256 == sha256(bytes) else {
            throw ProbeError("Metal pipeline cache integrity failure: \(key)")
        }
        return record
    }
}
func pipelineCacheRequest(device: MTLDevice, source: String, entry: String, residentStride: Int) throws -> PipelineCacheRequest? {
    let env = ProcessInfo.processInfo.environment
    let required = env["NIKKE_METAL_PIPELINE_REQUIRED"] == "1"
    guard let directory = env["NIKKE_METAL_PIPELINE_CACHE"], !directory.isEmpty else {
        if required { throw ProbeError("Required Metal pipeline cache needs a directory") }
        return nil
    }
    let identity = ["schema": "1", "source_sha256": sha256(Data(source.utf8)),
        "consumer_sha256": sha256(try Data(contentsOf: URL(fileURLWithPath: #filePath))),
        "entry": entry, "resident_stride": String(residentStride),
        "threads_per_threadgroup": String(portableThreadsPerThreadgroup), "math_mode": "safe",
        "registry_id": String(device.registryID), "device": device.name,
        "os_build": ProcessInfo.processInfo.operatingSystemVersionString]
    return PipelineCacheRequest(root: URL(fileURLWithPath: directory, isDirectory: true),
        identity: identity, key: sha256(try canonicalJSON(identity)), required: required)
}
func publishCacheFile(_ temporary: URL, _ destination: URL) throws {
    let file = try FileHandle(forWritingTo: temporary)
    try file.synchronize(); try file.close()
    guard chmod(temporary.path, 0o600) == 0, Darwin.rename(temporary.path, destination.path) == 0 else {
        throw ProbeError("Cannot publish Metal pipeline cache: \(errno)")
    }
}

// Preserve atomic publication without copying the whole GPU buffer into Data.
let portableReadbackChunkBytes = 8 * 1024 * 1024
func writeReadback(_ pointer: UnsafeMutableRawPointer, _ size: Int, _ path: String) throws {
    let temporary = path + "." + UUID().uuidString + ".writing"
    let fd = Darwin.open(temporary, O_WRONLY | O_CREAT | O_EXCL, mode_t(0o600))
    guard fd >= 0 else { throw ProbeError("Cannot create readback staging file: \(errno)") }
    let file = FileHandle(fileDescriptor: fd, closeOnDealloc: true)
    // Keep an incomplete staging file on error for inspection.
    for offset in stride(from: 0, to: size, by: portableReadbackChunkBytes) {
        let count = min(portableReadbackChunkBytes, size - offset)
        let chunk = Data(bytesNoCopy: pointer.advanced(by: offset), count: count, deallocator: .none)
        try file.write(contentsOf: chunk)
    }
    try file.synchronize()
    try file.close()
    guard Darwin.rename(temporary, path) == 0 else { throw ProbeError("Cannot publish readback file: \(errno)") }
}

// Serialize pipeline creation across worker processes. A concurrent cold
// compile of the same large kernel can stall in the Metal compiler service.
// Release before buffer encoding/dispatch; GPU work is not held by this lock.
func compilePipeline(device: MTLDevice, source: String, entry: String, lockURL: URL, residentStride: Int = 0) throws
    -> (pipeline: MTLComputePipelineState, librarySeconds: Double, pipelineSeconds: Double, lockWaitSeconds: Double, cache: [String: Any]?) {
    let cache = try pipelineCacheRequest(device: device, source: source, entry: entry, residentStride: residentStride)
    // Read both files only under the per-key lock, so a concurrent publisher's
    // archive/receipt handoff cannot look like a corrupt incomplete entry.
    // A required miss still stops before library compilation.
    if let cache = cache {
        if cache.required && !FileManager.default.fileExists(atPath: cache.root.path) {
            throw ProbeError("Required Metal pipeline cache miss: \(cache.key)")
        }
        try FileManager.default.createDirectory(at: cache.root, withIntermediateDirectories: true)
    }
    let actualLock = cache.map { $0.root.appendingPathComponent($0.key + ".lock") } ?? lockURL
    let descriptor = open(actualLock.path, O_CREAT | O_RDWR, 0o600)
    guard descriptor >= 0 else { throw ProbeError("Cannot open Metal pipeline lock") }
    defer { close(descriptor) }
    FileHandle.standardError.write(Data("portable_stage=pipeline_lock\n".utf8))
    let lockStart = Date().timeIntervalSinceReferenceDate
    while flock(descriptor, LOCK_EX) != 0 {
        if errno != EINTR { throw ProbeError("Cannot acquire Metal pipeline lock") }
    }
    let lockWaitSeconds = Date().timeIntervalSinceReferenceDate - lockStart
    defer { flock(descriptor, LOCK_UN) }
    let cached = try cache?.read()
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
    var pipelineOptions: MTLPipelineOption = residentStride > 0 ? [.argumentInfo, .bufferTypeInfo] : []
    var archive: MTLBinaryArchive?
    var archiveSeconds = 0.0
    if let cache = cache {
        let archiveDescriptor = MTLBinaryArchiveDescriptor()
        if cached != nil { archiveDescriptor.url = cache.archiveURL }
        archive = try device.makeBinaryArchive(descriptor: archiveDescriptor)
        pipelineDescriptor.binaryArchives = [archive!]
        if cached == nil {
            FileHandle.standardError.write(Data("portable_stage=pipeline_archive_compile\n".utf8))
            let start = Date().timeIntervalSinceReferenceDate
            try archive!.addComputePipelineFunctions(descriptor: pipelineDescriptor)
            archiveSeconds = Date().timeIntervalSinceReferenceDate - start
        }
        // A hit is proven by the native API, not by file existence or timing.
        pipelineOptions.insert(.failOnBinaryArchiveMiss)
    }
    let pipeline: MTLComputePipelineState
    do { pipeline = try device.makeComputePipelineState(descriptor: pipelineDescriptor, options: pipelineOptions, reflection: &reflection) }
    catch {
        if cache != nil { throw ProbeError("Metal binary archive pipeline failure: \(error)") }
        throw error
    }
    if residentStride > 0 {
        guard let state = reflection?.arguments.first(where: { $0.type == .buffer && $0.index == 2 }),
              state.bufferDataSize == residentStride else {
            throw ProbeError("Resident Runtime physical Metal layout differs from Slang reflection")
        }
    }
    let pipelineSeconds = Date().timeIntervalSinceReferenceDate - pipelineStart
    var cacheInfo: [String: Any]?
    if let cache = cache {
        var record = cached
        if record == nil {
            let temporary = cache.root.appendingPathComponent(cache.key + "." + UUID().uuidString + ".writing")
            try archive!.serialize(to: temporary)
            let bytes = try Data(contentsOf: temporary)
            guard !bytes.isEmpty else { throw ProbeError("Empty Metal pipeline archive") }
            try publishCacheFile(temporary, cache.archiveURL)
            record = PipelineCacheRecord(identity: cache.identity, archive_sha256: sha256(bytes), archive_bytes: bytes.count)
            let recordTemporary = cache.root.appendingPathComponent(cache.key + "." + UUID().uuidString + ".json.writing")
            try JSONEncoder().encode(record!).write(to: recordTemporary, options: .withoutOverwriting)
            try publishCacheFile(recordTemporary, cache.recordURL)
        }
        cacheInfo = ["schema": 1, "enabled": true, "required": cache.required, "hit": cached != nil,
            "key": cache.key, "identity": cache.identity, "archive_sha256": record!.archive_sha256,
            "archive_bytes": record!.archive_bytes, "native_archive_miss_rejected": true,
            "archive_compile_seconds": archiveSeconds]
    }
    return (pipeline, librarySeconds, pipelineSeconds, lockWaitSeconds, cacheInfo)
}

func run() throws {
    guard [4, 7, 8].contains(CommandLine.arguments.count) else { throw ProbeError("Expected: shader.metal input.bin output.bin [entry inputWords outputWords]") }
    let entry = CommandLine.arguments.count >= 7 ? CommandLine.arguments[4] : "portableProbe"
    let inputWords = CommandLine.arguments.count >= 7 ? Int(CommandLine.arguments[5]) ?? 0 : 97
    let outputWords = CommandLine.arguments.count >= 7 ? Int(CommandLine.arguments[6]) ?? 0 : 7
    let residentStride = CommandLine.arguments.count == 8 ? Int(CommandLine.arguments[7]) ?? 0 : 0
    guard CommandLine.arguments.count != 8 || (residentStride > 0 && residentStride <= 1048576 && residentStride % 8 == 0) else { throw ProbeError("Invalid resident stride") }
    guard inputWords > 0 && inputWords <= 131072 && outputWords > 0 && (outputWords <= 524288 || outputWords == 655360 || outputWords == 786432 || outputWords == 1048576 || outputWords == 1310720 || outputWords == 1507328 || outputWords == 1769472 || outputWords == 1769856 || outputWords == 2032000 || outputWords == 2064786) else { throw ProbeError("Invalid wire layout") }
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
        try writeReadback(output.contents(), outputSize, path["output"]!)
        var status: [String: Any] = ["backend": "metal", "device": device.name, "cases": count,
            "command_status": "completed", "registry_id": String(device.registryID),
            "gpu_seconds": command.gpuEndTime - command.gpuStartTime,
            "configured_max_threads_per_threadgroup": portableThreadsPerThreadgroup,
            "threads_per_threadgroup": portableThreadsPerThreadgroup,
            "pipeline_max_threads_per_threadgroup": pipeline.maxTotalThreadsPerThreadgroup,
            "library_compile_seconds": compiled.librarySeconds, "pipeline_compile_seconds": compiled.pipelineSeconds,
            "pipeline_lock_wait_seconds": compiled.lockWaitSeconds,
            "input_bytes": inputData.count, "output_bytes": outputSize,
            "file_readback_chunk_bytes": portableReadbackChunkBytes]
        if residentStride > 0 {
            status["runtime_stride_bytes"] = residentStride
            status["runtime_buffer_bytes"] = runtimeBytes
            status["runtime_element_capacity"] = maxCount
            status["runtime_physical_stride_verified"] = true
        }
        if let cache = compiled.cache {
            status["pipeline_cache"] = cache
            status["pipeline_os_build"] = ProcessInfo.processInfo.operatingSystemVersionString
        }
        statuses.append(status)
    }
    let result: [String: Any] = sequence ? ["batches": statuses, "pipeline_instances": 1, "buffer_allocations": residentStride > 0 ? 3 : 2] : statuses[0]
    print(String(data: try JSONSerialization.data(withJSONObject: result, options: [.sortedKeys]), encoding: .utf8)!)
}

do { try run() }
catch { FileHandle.standardError.write(Data("\(error)\n".utf8)); exit(1) }
