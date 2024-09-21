import argparse
import logging
import os
import platform
import re
import subprocess
import tempfile
from hashlib import sha1
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
JAVA_VERSION = 17


def get_java_executable(validate_java_version: bool) -> str:
    """
    Get the path to the Java executable. Optionally validates the Java version.

    :param validate_java_version: Whether to validate the Java version (should be >= 17).
    :return: Path to the Java executable.
    :raises Exception: If Java version is less than 17 or if Java is not found.
    """
    java_executable = "java"

    if "JAVA_HOME" in os.environ:
        java_exec_to_test = Path(os.environ["JAVA_HOME"]) / "bin" / "java"
        if java_exec_to_test.is_file():
            java_executable = str(java_exec_to_test.resolve())

    if not validate_java_version:
        return java_executable

    try:
        out = subprocess.check_output([java_executable, "-version"], stderr=subprocess.STDOUT, universal_newlines=True)
        java_major_version = next(
            int(match.group("major")) for match in re.finditer(r"(?<=version\s\")(?P<major>\d+)", out)
        )
        if java_major_version < JAVA_VERSION:
            raise Exception(f"jdtls requires at least Java 17, but found Java {java_major_version}")
    except Exception as e:
        raise Exception(f"Could not determine Java version: {e}")

    return java_executable


def find_equinox_launcher(jdtls_base_directory: Path) -> Path:
    """
    Find the Equinox launcher JAR in the provided directory.

    :param jdtls_base_directory: Base directory where the launcher should be located.
    :return: Path to the Equinox launcher JAR.
    :raises Exception: If the launcher is not found.
    """
    plugins_dir = jdtls_base_directory / "plugins"
    launchers = list(plugins_dir.glob("org.eclipse.equinox.launcher_*.jar"))

    if not launchers:
        raise Exception(f"Cannot find equinox launcher in {plugins_dir}")

    return launchers[0]


def get_shared_config_path(jdtls_base_path: Path) -> Path:
    """
    Get the shared configuration path based on the current platform.

    :param jdtls_base_path: Base path of the JDT LS.
    :return: Path to the shared configuration for the specific platform.
    :raises Exception: If the platform is unsupported.
    """
    system = platform.system()

    config_map = {
        "Linux": "config_linux",
        "FreeBSD": "config_linux",
        "Darwin": "config_mac",
        "Windows": "config_win",
    }

    config_dir = config_map.get(system)
    if not config_dir:
        raise Exception(f"Unknown platform {system} detected")

    return jdtls_base_path / config_dir


def main(args) -> None:
    """
    Main entry point for setting up and running JDT LS.

    :param args: Command-line arguments.
    """
    cwd_name = os.path.basename(os.getcwd())
    jdtls_data_path = Path(tempfile.gettempdir()) / f"jdtls-{sha1(cwd_name.encode()).hexdigest()}"

    parser = argparse.ArgumentParser(description="Run the Eclipse JDT Language Server.")
    parser.add_argument("--validate-java-version", action="store_true", default=True, help="Validate the Java version")
    parser.add_argument(
        "--no-validate-java-version",
        dest="validate_java_version",
        action="store_false",
        help="Skip Java version validation",
    )
    parser.add_argument("-data", default=jdtls_data_path, help="Data directory for JDT LS")

    known_args, unknown_args = parser.parse_known_args(args)

    java_executable = get_java_executable(known_args.validate_java_version)

    jdtls_base_path = Path(__file__).parent.parent
    shared_config_path = get_shared_config_path(jdtls_base_path)
    jar_path = find_equinox_launcher(jdtls_base_path)

    logging.info("Starting JDT LS with Java executable: %s", java_executable)

    exec_args = [
        "-Declipse.application=org.eclipse.jdt.ls.core.id1",
        "-Dosgi.bundles.defaultStartLevel=4",
        "-Declipse.product=org.eclipse.jdt.ls.core.product",
        "-Dosgi.checkConfiguration=true",
        f"-Dosgi.sharedConfiguration.area={shared_config_path}",
        "-Dosgi.sharedConfiguration.area.readOnly=true",
        "-Dosgi.configuration.cascaded=true",
        "-Xms1G",
        "--add-modules=ALL-SYSTEM",
        "--add-opens",
        "java.base/java.util=ALL-UNNAMED",
        "--add-opens",
        "java.base/java.lang=ALL-UNNAMED",
        f"-javaagent:{jdtls_base_path}/plugins/lombok-edge.jar",
        "-jar",
        str(jar_path),
        "-data",
        str(known_args.data),
    ] + unknown_args

    logging.info("Executing with args: %s", exec_args)

    result = subprocess.run([java_executable] + exec_args, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        logging.error("Error running JDT LS: %s", result.stderr)
        raise Exception(f"Failed to run JDT LS: {result.stderr}")
    else:
        logging.info("JDT LS started successfully.")
