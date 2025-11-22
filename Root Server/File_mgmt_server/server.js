import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { exec as callbackExec } from "node:child_process";
import { promisify } from "node:util";
import { z } from "zod";
import { writeFileSync, appendFileSync } from "node:fs";

// Clear the log file when server starts
writeFileSync("debug.log", "=== Server Started ===\n");

const server = new McpServer({
    name: "file_management_mcp_server",
    version: "1.0.0",
    capabilities: {
        resources: {},
        tools: {},
    },
});

const exec = promisify(callbackExec);

server.tool(
    "read_file",
    "This tool reads the content of a specified file. Provide the file path as 'file_path' to read it.",
    {
        file_path: z.string().describe("The path of the file to read."),
    },
    async (input) => {
        appendFileSync("debug.log", `DEBUG: read_file called with: ${input.file_path}\n`);
        
        if (!input.file_path) {
            appendFileSync("debug.log", "DEBUG: Missing file_path\n");
            return { content: [{ type: "text", text: "Missing file_path." }] };
        }
        
        try {
            const command = `powershell.exe -ExecutionPolicy Bypass -File "C:\\Users\\jaymi\\OneDrive\\Documents\\Programs\\Projects\\Complete UI Automation\\Root Server\\File_mgmt_server\\tools\\read_file.ps1" -FilePath "${input.file_path}"`;
            appendFileSync("debug.log", `DEBUG: Executing command: ${command}\n`);
            
            const { stdout, stderr } = await exec(command);
            appendFileSync("debug.log", `DEBUG: stdout: ${stdout}\n`);
            appendFileSync("debug.log", `DEBUG: stderr: ${stderr}\n`);
            
            const response = JSON.parse(stdout.trim());
            appendFileSync("debug.log", `DEBUG: Parsed response: ${JSON.stringify(response)}\n`);

            if (!response.success) {
                appendFileSync("debug.log", "DEBUG: Response not successful\n");
                return {
                    content: [
                        { type: "text", text: `Error reading file:\n${response.message}` }
                    ]
                };
            }

            appendFileSync("debug.log", "DEBUG: Returning success\n");
            return {
                content: [
                    {
                        type: "text",
                        text: `File content:\n${response.data.value}`,
                    },
                ],
            };
        } catch (error) {
            appendFileSync("debug.log", `DEBUG: Caught error: ${error}\n`);
            appendFileSync("debug.log", `DEBUG: Error message: ${error.message}\n`);
            appendFileSync("debug.log", `DEBUG: Error stack: ${error.stack}\n`);
            return {
                content: [
                    {
                        type: "text",
                        text: `Failed to read file: ${error.message}`,
                    },
                ],
            };
        }
    }
)

server.tool(
    "list_items",
    "This tool lists all files and directories at the specified path. Provide the directory path as 'directory_path' to list its items.",
    {
        directory_path: z.string().describe("The path of the directory to list items from."),
    },
    async (input) => {
        if (!input.directory_path) {
            return { content: [{ type: "text", text: "Missing directory_path." }] };
        }
        try {
            const command = `powershell.exe -ExecutionPolicy Bypass -File "C:\\Users\\jaymi\\OneDrive\\Documents\\Programs\\Projects\\Complete UI Automation\\Root Server\\File_mgmt_server\\tools\\list_items.ps1" -DirectoryPath "${input.directory_path}"`;
            const result = await exec(command);
            const response = JSON.parse(result.stdout.trim());

            if (!response.success) {
                return {
                    content: [
                        { type: "text", text: `Error listing items:\n${response.message}` }
                    ]
                };
            }

            return {
                content: [
                    {
                        type: "text",
                        text: JSON.stringify(response.data),
                    }
                ]
            }
        } catch (error) {
            return {
                content: [
                    {
                        type: "text",
                        text: `Failed to list items: ${error.message}`,
                    },
                ],
            };
        }
    }
)

server.tool(
    "edit_file",
    "This tool writes content to a specified file. Provide the file path as 'file_path' and the content as 'content' to write or edit the file.",
    {
        file_path: z.string().describe("The path of the file to write or edit."),
        content: z.string().describe("The content to write into the file."),
    },
    async (input) => {
        if (!input.file_path || !input.content) {
            return { content: [{ type: "text", text: "Missing file_path or content." }] };
        }
        try {
            const command = `powershell.exe -ExecutionPolicy Bypass -File "C:\\Users\\jaymi\\OneDrive\\Documents\\Programs\\Projects\\Complete UI Automation\\Root Server\\File_mgmt_server\\tools\\edit_file.ps1" -FilePath "${input.file_path}" -NewContent "${input.content.replace(/"/g, '\\"')}"`;
            const result = await exec(command);
            const response = JSON.parse(result.stdout.trim());
            if (!response.success) {
                return {
                    content: [
                        { type: "text", text: `Error writing or editing file:\n${response.message}` }
                    ]
                };
            }

            return {
                content: [
                    {
                        type: "text",
                        text: `File written/edited successfully.`,
                    },
                ],
            };
        } catch (error) {
            return {
                content: [
                    {
                        type: "text",
                        text: `Failed to write or edit file: ${error.message}`,
                    },
                ],
            };
        }
    }
)

server.connect(new StdioServerTransport())
    .then(() => {
    console.error("MCP Server is running...");
})
    .catch((error) => {
    console.error("Failed to start MCP Server:", error);
});