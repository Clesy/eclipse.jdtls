#!/usr/bin/env bash

set -e

# Ensure JAVA_HOME is set
if [ -z "${JAVA_HOME:-}" ]; then
    echo "Error: JAVA_HOME is not set. Please set it to your Java installation path."
    exit 1
fi

# Clean the dist directory
rm -rf dist
mkdir -p dist

# Build the JDT LS
pushd eclipse.jdt.ls/ > /dev/null
JAVA_HOME="$JAVA_HOME" ./mvnw clean verify -DskipTests
popd > /dev/null

# Download lombok-edge.jar and put it in the plugins directory
Lombok_JAR_URL="https://projectlombok.org/lombok-edge.jar"
curl -L -o lombok-edge.jar "$Lombok_JAR_URL"
mv lombok-edge.jar ./eclipse.jdt.ls/org.eclipse.jdt.ls.product/target/repository/plugins/

# Replace jdtls wrapper script
cp -f jdtls.py ./eclipse.jdt.ls/org.eclipse.jdt.ls.product/target/repository/bin/jdtls.py

# Create the tar.gz
tar -czf dist/eclipse.jdt.ls.tar.gz -C eclipse.jdt.ls/org.eclipse.jdt.ls.product/target/repository .

# Prepare for the .zip creation
mkdir -p dist/eclipse.jdt.ls
cp -r eclipse.jdt.ls/org.eclipse.jdt.ls.product/target/repository/* dist/eclipse.jdt.ls/

# Create the .zip
pushd dist > /dev/null
zip -r eclipse.jdt.ls.zip eclipse.jdt.ls
popd > /dev/null
