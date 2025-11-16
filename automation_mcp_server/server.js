import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { exec as callbackExec } from "node:child_process";
import { promisify } from "node:util";
import { z } from "zod";

const server = new McpServer({
  name: "automation_mcp_server",
  version: "1.0.0",
  capabilities: {
    resources: {},
    tools: {},
  },
});

const exec = promisify(callbackExec);

server.tool(
  "open_software",
  "This tool opens a specified software application on windows. Provide the name of the application as 'name' to open it in js.",
  {
    name: z.string().describe("The name of the software application to open."),
  },
  async (input) => {
    try {
      const command = `powershell.exe -ExecutionPolicy Bypass -File "C:\\Users\\jaymi\\OneDrive\\Documents\\Programs\\Projects\\Complete UI Automation\\automation_mcp_server\\open_software.ps1" -AppName "${input.name}"`;

      await exec(command);

      return {
        content: [
          {
            type: "text",
            text: "Application opened successfully",
          },
        ],
      };
    } catch (error) {
      console.error("Error while opening application:", error);

      return {
        content: [
          {
            type: "text",
            text: "Failed to open application",
          },
        ],
      };
      // throw new Error(
      //   `Failed to open application: ${input.name}. PowerShell script failed to find the app.`
      // );
    }
  }
);

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("Automation MCP Server is running and connected.");
}

main().catch((error) => {
  console.error("Fatal error in main():", error);
  process.exit(1);
});
