#!/usr/bin/env python3
"""
Generates SonicWaveReceiver.xcodeproj/project.pbxproj
"""

import os

def create_project():
    proj_dir = os.path.dirname(os.path.abspath(__file__))
    xcodeproj_dir = os.path.join(proj_dir, "SonicWaveReceiver.xcodeproj")
    os.makedirs(xcodeproj_dir, exist_ok=True)
    
    pbxproj_path = os.path.join(xcodeproj_dir, "project.pbxproj")
    
    # IDs
    proj_id = "010000000000000000000001"
    target_id = "010000000000000000000002"
    config_list_proj = "010000000000000000000003"
    config_list_target = "010000000000000000000004"
    config_debug_proj = "010000000000000000000005"
    config_release_proj = "010000000000000000000006"
    config_debug_target = "010000000000000000000007"
    config_release_target = "010000000000000000000008"
    
    group_main = "010000000000000000000010"
    group_src = "010000000000000000000011"
    group_views = "010000000000000000000012"
    group_audio = "010000000000000000000013"
    group_dsp = "010000000000000000000014"
    group_models = "010000000000000000000015"
    group_products = "010000000000000000000016"
    
    build_sources = "010000000000000000000020"
    build_frameworks = "010000000000000000000021"
    build_resources = "010000000000000000000022"
    
    product_ref = "010000000000000000000030"
    
    files = [
        ("SonicWaveReceiverApp.swift", "010000000000000000000101", "010000000000000000000201", group_src),
        ("Views/ContentView.swift", "010000000000000000000102", "010000000000000000000202", group_views),
        ("Audio/SonicWaveAudioEngine.swift", "010000000000000000000103", "010000000000000000000203", group_audio),
        ("DSP/SonicWaveDSPCore.swift", "010000000000000000000104", "010000000000000000000204", group_dsp),
        ("DSP/CRC16.swift", "010000000000000000000105", "010000000000000000000205", group_dsp),
        ("Models/DecodedMessage.swift", "010000000000000000000106", "010000000000000000000206", group_models),
    ]
    
    info_plist_ref = "010000000000000000000107"
    
    pbx = f"""// !$*UTF8*$!
{{
	archiveVersion = 1;
	classes = {{
	}};
	objectVersion = 56;
	objects = {{

/* Begin PBXBuildFile section */
"""
    for fname, fref, bref, _ in files:
        basename = os.path.basename(fname)
        pbx += f"\t\t{bref} /* {basename} in Sources */ = {{isa = PBXBuildFile; fileRef = {fref} /* {basename} */; }};\n"
        
    pbx += f"""/* End PBXBuildFile section */

/* Begin PBXFileReference section */
\t\t{product_ref} /* SonicWaveReceiver.app */ = {{isa = PBXFileReference; explicitFileType = wrapper.application; includeInIndex = 0; path = SonicWaveReceiver.app; sourceTree = BUILT_PRODUCTS_DIR; }};
\t\t{info_plist_ref} /* Info.plist */ = {{isa = PBXFileReference; lastKnownFileType = text.plist.xml; path = Info.plist; sourceTree = "<group>"; }};
"""
    for fname, fref, _, _ in files:
        basename = os.path.basename(fname)
        pbx += f"\t\t{fref} /* {basename} */ = {{isa = PBXFileReference; lastKnownFileType = sourcecode.swift; path = \"{basename}\"; sourceTree = \"<group>\"; }};\n"

    pbx += f"""/* End PBXFileReference section */

/* Begin PBXFrameworksBuildPhase section */
\t\t{build_frameworks} /* Frameworks */ = {{
\t\t\tisa = PBXFrameworksBuildPhase;
\t\t\tbuildActionMask = 2147483647;
\t\t\tfiles = (
\t\t\t);
\t\t\trunOnlyForDeploymentPostprocessing = 0;
\t\t}};
/* End PBXFrameworksBuildPhase section */

/* Begin PBXGroup section */
\t\t{group_main} = {{
\t\t\tisa = PBXGroup;
\t\t\tchildren = (
\t\t\t\t{group_src} /* SonicWaveReceiver */,
\t\t\t\t{group_products} /* Products */,
\t\t\t);
\t\t\tsourceTree = "<group>";
\t\t}};
\t\t{group_products} /* Products */ = {{
\t\t\tisa = PBXGroup;
\t\t\tchildren = (
\t\t\t\t{product_ref} /* SonicWaveReceiver.app */,
\t\t\t);
\t\t\tname = Products;
\t\t\tsourceTree = "<group>";
\t\t}};
\t\t{group_src} /* SonicWaveReceiver */ = {{
\t\t\tisa = PBXGroup;
\t\t\tchildren = (
\t\t\t\t010000000000000000000101 /* SonicWaveReceiverApp.swift */,
\t\t\t\t{group_views} /* Views */,
\t\t\t\t{group_audio} /* Audio */,
\t\t\t\t{group_dsp} /* DSP */,
\t\t\t\t{group_models} /* Models */,
\t\t\t\t{info_plist_ref} /* Info.plist */,
\t\t\t);
\t\t\tpath = SonicWaveReceiver;
\t\t\tsourceTree = "<group>";
\t\t}};
\t\t{group_views} /* Views */ = {{
\t\t\tisa = PBXGroup;
\t\t\tchildren = (
\t\t\t\t010000000000000000000102 /* ContentView.swift */,
\t\t\t);
\t\t\tpath = Views;
\t\t\tsourceTree = "<group>";
\t\t}};
\t\t{group_audio} /* Audio */ = {{
\t\t\tisa = PBXGroup;
\t\t\tchildren = (
\t\t\t\t010000000000000000000103 /* SonicWaveAudioEngine.swift */,
\t\t\t);
\t\t\tpath = Audio;
\t\t\tsourceTree = "<group>";
\t\t}};
\t\t{group_dsp} /* DSP */ = {{
\t\t\tisa = PBXGroup;
\t\t\tchildren = (
\t\t\t\t010000000000000000000104 /* SonicWaveDSPCore.swift */,
\t\t\t\t010000000000000000000105 /* CRC16.swift */,
\t\t\t);
\t\t\tpath = DSP;
\t\t\tsourceTree = "<group>";
\t\t}};
\t\t{group_models} /* Models */ = {{
\t\t\tisa = PBXGroup;
\t\t\tchildren = (
\t\t\t\t010000000000000000000106 /* DecodedMessage.swift */,
\t\t\t);
\t\t\tpath = Models;
\t\t\tsourceTree = "<group>";
\t\t}};
/* End PBXGroup section */

/* Begin PBXNativeTarget section */
\t\t{target_id} /* SonicWaveReceiver */ = {{
\t\t\tisa = PBXNativeTarget;
\t\t\tbuildConfigurationList = {config_list_target} /* Build configuration list for PBXNativeTarget "SonicWaveReceiver" */;
\t\t\tbuildPhases = (
\t\t\t\t{build_sources} /* Sources */,
\t\t\t\t{build_frameworks} /* Frameworks */,
\t\t\t\t{build_resources} /* Resources */,
\t\t\t);
\t\t\tbuildRules = (
\t\t\t);
\t\t\tdependencies = (
\t\t\t);
\t\t\tname = SonicWaveReceiver;
\t\t\tproductName = SonicWaveReceiver;
\t\t\tproductReference = {product_ref} /* SonicWaveReceiver.app */;
\t\t\tproductType = "com.apple.product-type.application";
\t\t}};
/* End PBXNativeTarget section */

/* Begin PBXProject section */
\t\t{proj_id} /* Project object */ = {{
\t\t\tisa = PBXProject;
\t\t\tattributes = {{
\t\t\t\tBuildIndependentTargetsInParallel = 1;
\t\t\t\tLastUpgradeCheck = 1500;
\t\t\t\tTargetAttributes = {{
\t\t\t\t\t{target_id} = {{
\t\t\t\t\t\tCreatedOnToolsVersion = 15.0;
\t\t\t\t\t}};
\t\t\t\t}};
\t\t\t}};
\t\t\tbuildConfigurationList = {config_list_proj} /* Build configuration list for PBXProject "SonicWaveReceiver" */;
\t\t\tcompatibilityVersion = "Xcode 14.0";
\t\t\tdevelopmentRegion = en;
\t\t\thasScannedForEncodings = 0;
\t\t\tknownRegions = (
\t\t\t\ten,
\t\t\t\tBase,
\t\t\t);
\t\t\tmainGroup = {group_main};
\t\t\tproductRefGroup = {group_products} /* Products */;
\t\t\tprojectDirPath = "";
\t\t\tprojectRoot = "";
\t\t\ttargets = (
\t\t\t\t{target_id} /* SonicWaveReceiver */,
\t\t\t);
\t\t}};
/* End PBXProject section */

/* Begin PBXResourcesBuildPhase section */
\t\t{build_resources} /* Resources */ = {{
\t\t\tisa = PBXResourcesBuildPhase;
\t\t\tbuildActionMask = 2147483647;
\t\t\tfiles = (
\t\t\t);
\t\t\trunOnlyForDeploymentPostprocessing = 0;
\t\t}};
/* End PBXResourcesBuildPhase section */

/* Begin PBXSourcesBuildPhase section */
\t\t{build_sources} /* Sources */ = {{
\t\t\tisa = PBXSourcesBuildPhase;
\t\t\tbuildActionMask = 2147483647;
\t\t\tfiles = (
"""
    for fname, _, bref, _ in files:
        basename = os.path.basename(fname)
        pbx += f"\t\t\t\t{bref} /* {basename} in Sources */,\n"
        
    pbx += f"""\t\t\t);
\t\t\trunOnlyForDeploymentPostprocessing = 0;
\t\t}};
/* End PBXSourcesBuildPhase section */

/* Begin XCBuildConfiguration section */
\t\t{config_debug_proj} /* Debug */ = {{
\t\t\tisa = XCBuildConfiguration;
\t\t\tbuildSettings = {{
\t\t\t\tALWAYS_SEARCH_USER_PATHS = NO;
\t\t\t\tCLANG_ANALYZER_NONNULL = YES;
\t\t\t\tCLANG_CXX_LANGUAGE_STANDARD = "gnu++20";
\t\t\t\tCLANG_ENABLE_MODULES = YES;
\t\t\t\tCLANG_ENABLE_OBJC_ARC = YES;
\t\t\t\tCOPY_PHASE_STRIP = NO;
\t\t\t\tDEBUG_INFORMATION_FORMAT = dwarf;
\t\t\t\tENABLE_STRICT_OBJC_MSGSEND = YES;
\t\t\t\tENABLE_TESTABILITY = YES;
\t\t\t\tGCC_DYNAMIC_NO_PIC = NO;
\t\t\t\tGCC_NO_COMMON_BLOCKS = YES;
\t\t\t\tGCC_OPTIMIZATION_LEVEL = 0;
\t\t\t\tGCC_PREPROCESSOR_DEFINITIONS = (
\t\t\t\t\t"DEBUG=1",
\t\t\t\t\t"$(inherited)",
\t\t\t\t);
\t\t\t\tIPHONEOS_DEPLOYMENT_TARGET = 16.0;
\t\t\t\tMTL_ENABLE_DEBUG_INFO = INCLUDE_SOURCE;
\t\t\t\tONLY_ACTIVE_ARCH = YES;
\t\t\t\tSDKROOT = iphoneos;
\t\t\t\tSWIFT_ACTIVE_COMPILATION_CONDITIONS = DEBUG;
\t\t\t\tSWIFT_OPTIMIZATION_LEVEL = "-Onone";
\t\t\t}};
\t\t\tname = Debug;
\t\t}};
\t\t{config_release_proj} /* Release */ = {{
\t\t\tisa = XCBuildConfiguration;
\t\t\tbuildSettings = {{
\t\t\t\tALWAYS_SEARCH_USER_PATHS = NO;
\t\t\t\tCLANG_ANALYZER_NONNULL = YES;
\t\t\t\tCLANG_CXX_LANGUAGE_STANDARD = "gnu++20";
\t\t\t\tCLANG_ENABLE_MODULES = YES;
\t\t\t\tCLANG_ENABLE_OBJC_ARC = YES;
\t\t\t\tCOPY_PHASE_STRIP = NO;
\t\t\t\tDEBUG_INFORMATION_FORMAT = "dwarf-with-dsym";
\t\t\t\tENABLE_NS_ASSERTIONS = NO;
\t\t\t\tENABLE_STRICT_OBJC_MSGSEND = YES;
\t\t\t\tGCC_NO_COMMON_BLOCKS = YES;
\t\t\t\tIPHONEOS_DEPLOYMENT_TARGET = 16.0;
\t\t\t\tMTL_ENABLE_DEBUG_INFO = NO;
\t\t\t\tSDKROOT = iphoneos;
\t\t\t\tSWIFT_COMPILATION_MODE = wholemodule;
\t\t\t\tSWIFT_OPTIMIZATION_LEVEL = "-O";
\t\t\t\tVALIDATE_PRODUCT = YES;
\t\t\t}};
\t\t\tname = Release;
\t\t}};
\t\t{config_debug_target} /* Debug */ = {{
\t\t\tisa = XCBuildConfiguration;
\t\t\tbuildSettings = {{
\t\t\t\tASSETCATALOG_COMPILER_APPICON_NAME = AppIcon;
\t\t\t\tASSETCATALOG_COMPILER_GLOBAL_ACCENT_COLOR_NAME = AccentColor;
\t\t\t\tCODE_SIGN_STYLE = Automatic;
\t\t\t\tCURRENT_PROJECT_VERSION = 1;
\t\t\t\tDEVELOPMENT_TEAM = "";
\t\t\t\tENABLE_PREVIEWS = YES;
\t\t\t\tGENERATE_INFOPLIST_FILE = NO;
\t\t\t\tINFOPLIST_FILE = SonicWaveReceiver/Info.plist;
\t\t\t\tINFOPLIST_KEY_NSMicrophoneUsageDescription = "SonicWave requires microphone access to capture and decode silent ultrasonic data transmissions.";
\t\t\t\tLD_RUNPATH_SEARCH_PATHS = (
\t\t\t\t\t"$(inherited)",
\t\t\t\t\t"@executable_path/Frameworks",
\t\t\t\t);
\t\t\t\tMARKETING_VERSION = 1.0;
\t\t\t\tPRODUCT_BUNDLE_IDENTIFIER = com.sonicwave.receiver;
\t\t\t\tPRODUCT_NAME = "$(TARGET_NAME)";
\t\t\t\tSWIFT_EMIT_LOC_STRINGS = YES;
\t\t\t\tSWIFT_VERSION = 5.0;
\t\t\t\tTARGETED_DEVICE_FAMILY = "1,2";
\t\t\t}};
\t\t\tname = Debug;
\t\t}};
\t\t{config_release_target} /* Release */ = {{
\t\t\tisa = XCBuildConfiguration;
\t\t\tbuildSettings = {{
\t\t\t\tASSETCATALOG_COMPILER_APPICON_NAME = AppIcon;
\t\t\t\tASSETCATALOG_COMPILER_GLOBAL_ACCENT_COLOR_NAME = AccentColor;
\t\t\t\tCODE_SIGN_STYLE = Automatic;
\t\t\t\tCURRENT_PROJECT_VERSION = 1;
\t\t\t\tDEVELOPMENT_TEAM = "";
\t\t\t\tENABLE_PREVIEWS = YES;
\t\t\t\tGENERATE_INFOPLIST_FILE = NO;
\t\t\t\tINFOPLIST_FILE = SonicWaveReceiver/Info.plist;
\t\t\t\tINFOPLIST_KEY_NSMicrophoneUsageDescription = "SonicWave requires microphone access to capture and decode silent ultrasonic data transmissions.";
\t\t\t\tLD_RUNPATH_SEARCH_PATHS = (
\t\t\t\t\t"$(inherited)",
\t\t\t\t\t"@executable_path/Frameworks",
\t\t\t\t);
\t\t\t\tMARKETING_VERSION = 1.0;
\t\t\t\tPRODUCT_BUNDLE_IDENTIFIER = com.sonicwave.receiver;
\t\t\t\tPRODUCT_NAME = "$(TARGET_NAME)";
\t\t\t\tSWIFT_EMIT_LOC_STRINGS = YES;
\t\t\t\tSWIFT_VERSION = 5.0;
\t\t\t\tTARGETED_DEVICE_FAMILY = "1,2";
\t\t\t}};
\t\t\tname = Release;
\t\t}};
/* End XCBuildConfiguration section */

/* Begin XCConfigurationList section */
\t\t{config_list_proj} /* Build configuration list for PBXProject "SonicWaveReceiver" */ = {{
\t\t\tisa = XCConfigurationList;
\t\t\tbuildConfigurations = (
\t\t\t\t{config_debug_proj} /* Debug */,
\t\t\t\t{config_release_proj} /* Release */,
\t\t\t);
\t\t\tdefaultConfigurationIsVisible = 0;
\t\t\tdefaultConfigurationName = Release;
\t\t}};
\t\t{config_list_target} /* Build configuration list for PBXNativeTarget "SonicWaveReceiver" */ = {{
\t\t\tisa = XCConfigurationList;
\t\t\tbuildConfigurations = (
\t\t\t\t{config_debug_target} /* Debug */,
\t\t\t\t{config_release_target} /* Release */,
\t\t\t);
\t\t\tdefaultConfigurationIsVisible = 0;
\t\t\tdefaultConfigurationName = Release;
\t\t}};
/* End XCConfigurationList section */

\t}};
\trootObject = {proj_id} /* Project object */;
}}
"""
    with open(pbxproj_path, "w") as f:
        f.write(pbx)
    print(f"Created Xcode project: {xcodeproj_dir}")

if __name__ == "__main__":
    create_project()
