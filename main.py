name: Android Build

on: [push]

jobs:
  build:
    # Use Ubuntu for a stable build environment
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
      
    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.10'
        
    - name: Install dependencies
      run: |
        # Install all system dependencies required for Buildozer
        sudo apt-get update
        sudo apt-get install -y git zip unzip openjdk-17-jdk python3-pip autoconf libtool pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo5
        pip install buildozer
        
    - name: 💥 CRITICAL FIX: Force API 28 💥
      run: |
        # Fixes the AC_PROG_LD error and the ANDROID_API __21 warning.
        # This overwrites the values in your buildozer.spec (currently minapi=21)
        sed -i 's/android.minapi = 21/android.minapi = 28/g' buildozer.spec
        sed -i 's/android.ndk_api = 21/android.ndk_api = 28/g' buildozer.spec
        
    - name: Run Buildozer
      run: |
        # Run the Android debug build
        buildozer android debug

    - name: Upload APK Artifact
      uses: actions/upload-artifact@v4
      with:
        name: mgbroadcast-apk
        path: bin/*.apk
