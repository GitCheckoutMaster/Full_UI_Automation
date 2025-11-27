import {McpServer} from "@modelcontextprotocol/sdk/server/mcp.js";
import {StdioServerTransport} from "@modelcontextprotocol/sdk/server/stdio.js";
import {exec as callbackExec} from "node:child_process";
import {promisify} from "node:util";
import {file, z} from "zod";
import {writeFileSync, appendFileSync} from "node:fs";

const server = new McpServer({
    name: "vscode_mcp_server",
    version: "1.0.0",
    capabilities: {
        resources: {},
        tools: {},
    },
});

const exec = promisify(callbackExec);

server.tool(
    "open_file_in_vscode",
    "This tool opens a specified file in Visual Studio Code. Provide the file path as 'file_path' to open it.(if path does not exists, it will be created)",
    {
        file_path: z.string().describe("The path of the file to open in VS Code."),
    },
    async ({file_path}) => {
        if (!file_path) {
            return {content: [{type: "text", text: "Missing file_path."}]};
        }
        try {
            const command = `powershell.exe -ExecutionPolicy Bypass -File "C:\\Users\\jaymi\\OneDrive\\Documents\\Programs\\Projects\\Complete UI Automation\\Root Server\\VS_code_server\\tools\\open_file.ps1" -FilePath "${file_path}"`;
            const {stdout, stderr} = await exec(command);
            const response = JSON.parse(stdout.trim());

            if (!response.success) {
                return {
                    content: [
                        {type: "text", text: `Error opening file in VS Code:\n${response.message}`},
                    ],
                };
            }
            return {
                content: [
                    {type: "text", text: `File opened successfully in VS Code: ${file_path}`},
                ],
            };
        } catch (error) {
            return {
                content: [
                    {type: "text", text: `Exception occurred:\n${error.message}`},
                ],
            };
        }
    }
)

server.connect(new StdioServerTransport())
    .then(() => {
    console.error("VS code MCP Server is running...");
})
    .catch((error) => {
    console.error("Failed to start VS code MCP Server:", error);
});
