// Device enumeration only: no library, pipeline, buffer or command queue.
import Foundation
import Metal
import Darwin

let device = MTLCreateSystemDefaultDevice()
var result: [String: Any] = ["schema": "metal-device-visibility-v1",
    "device_visible": device != nil, "kernel_calls": 0]
if let device = device {
    result["device"] = device.name
    result["registry_id"] = String(device.registryID)
    result["max_buffer_length"] = device.maxBufferLength
}
let data = try JSONSerialization.data(withJSONObject: result, options: [.sortedKeys])
FileHandle.standardOutput.write(data)
FileHandle.standardOutput.write(Data([10]))
exit(device == nil ? 2 : 0)
