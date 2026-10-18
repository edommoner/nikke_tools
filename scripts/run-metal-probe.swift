// Metal transport only. All tested state transitions are in portable_probe.slang.
import Foundation
import Metal

struct ProbeError: Error, CustomStringConvertible {
    let description: String
    init(_ message: String) { description = message }
}

func run() throws {
    guard CommandLine.arguments.count == 4 else { throw ProbeError("Expected: shader.metal input.bin output.bin") }
    guard let device = MTLCreateSystemDefaultDevice() else { throw ProbeError("No Metal device") }
    let inputData = try Data(contentsOf: URL(fileURLWithPath: CommandLine.arguments[2]))
    guard inputData.count >= 4 else { throw ProbeError("Missing input header") }
    let count = inputData.withUnsafeBytes { UInt32(littleEndian: $0.loadUnaligned(as: UInt32.self)) }
    guard count > 0 && count <= 64 && inputData.count == (1 + Int(count) * 97) * 4 else { throw ProbeError("Invalid input dimensions") }
    let outputSize = Int(count) * 7 * 4
    guard let input = device.makeBuffer(length: inputData.count, options: .storageModeShared),
          let output = device.makeBuffer(length: outputSize, options: .storageModeShared),
          let queue = device.makeCommandQueue() else { throw ProbeError("Metal allocation failed") }
    inputData.withUnsafeBytes { bytes in input.contents().copyMemory(from: bytes.baseAddress!, byteCount: bytes.count) }
    output.contents().initializeMemory(as: UInt8.self, repeating: 0, count: outputSize)
    let source = try String(contentsOfFile: CommandLine.arguments[1], encoding: .utf8)
    let library = try device.makeLibrary(source: source, options: nil)
    guard let function = library.makeFunction(name: "portableProbe") else { throw ProbeError("Missing portableProbe entry") }
    let pipeline = try device.makeComputePipelineState(function: function)
    guard let command = queue.makeCommandBuffer(), let encoder = command.makeComputeCommandEncoder() else { throw ProbeError("Metal command creation failed") }
    encoder.setComputePipelineState(pipeline)
    encoder.setBuffer(input, offset: 0, index: 0)
    encoder.setBuffer(output, offset: 0, index: 1)
    encoder.dispatchThreadgroups(MTLSize(width: Int(count), height: 1, depth: 1), threadsPerThreadgroup: MTLSize(width: 1, height: 1, depth: 1))
    encoder.endEncoding()
    command.commit()
    command.waitUntilCompleted()
    guard command.status == .completed else { throw ProbeError(command.error?.localizedDescription ?? "Metal execution failed") }
    try Data(bytes: output.contents(), count: outputSize).write(to: URL(fileURLWithPath: CommandLine.arguments[3]), options: .atomic)
    let status: [String: Any] = ["backend": "metal", "device": device.name, "cases": count]
    print(String(data: try JSONSerialization.data(withJSONObject: status, options: [.sortedKeys]), encoding: .utf8)!)
}

do { try run() }
catch { FileHandle.standardError.write(Data("\(error)\n".utf8)); exit(1) }
