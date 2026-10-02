// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "SonicWaveReceiver",
    platforms: [
        .iOS(.v16),
        .macOS(.v13)
    ],
    products: [
        .library(
            name: "SonicWaveCore",
            targets: ["SonicWaveCore"]
        ),
    ],
    targets: [
        .target(
            name: "SonicWaveCore",
            path: "SonicWaveReceiver",
            sources: ["DSP", "Models"]
        ),
        .testTarget(
            name: "SonicWaveCoreTests",
            dependencies: ["SonicWaveCore"],
            path: "Tests"
        )
    ]
)
