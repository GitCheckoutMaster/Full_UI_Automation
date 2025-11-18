import { exec as callbackExec } from "node:child_process";
import { promisify } from "node:util";

const exec = promisify(callbackExec);

try {
    const command = `powershell.exe -ExecutionPolicy Bypass -File "tools\\read_file.ps1" -FilePath "C:\\Users\\jaymi\\OneDrive\\Documents\\test.txt"`;
    const { stdout } = await exec(command);
    const response = JSON.parse(stdout.trim());

    console.log("Command executed successfully:", response);
} catch (error) {
    console.error("Error executing command:", error);
}