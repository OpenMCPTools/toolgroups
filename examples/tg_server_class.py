from toolgroups import Group, ToolConverter, ToolgroupMCPServer
from mcp.types import ToolAnnotations

# create trusted group
trusted_groups=Group(name="trustedgroup",title="Trusted Toolgroups", description="The tools and toolgroups in this group are trusted by this server")

# Create server
tg_server = ToolgroupMCPServer("toolgroup server")

# use toolgroup class annotation and mcp.tool annotations for tools
@tg_server.toolgroup(parent=trusted_groups, title="Arithmetic", description="Arithmetic Group")
class Arithmetic:
    @tg_server.tool(title="Add X and Y Integer", annotations=ToolAnnotations(read_only_hint=True), structured_output=True)
    def add(self, x: int, y: int) -> int:
        ''' add two numbers'''
        return x + y
    
    @tg_server.tool(title="Multiply X and Y", annotations=ToolAnnotations(read_only_hint=True), structured_output=True)
    def multiply(self, x: int, y: int) -> int:
        '''multiply two numbers'''
        return x * y 

# run test client in memory
from mcp.client import Client
import asyncio

'''test with in memory client'''
async def main():
    async with Client(tg_server) as client:
        lr = await client.list_tools()
        print("Client received the following grouped tools")
        for t in ToolConverter().convert_to_list(lr.tools):
            for r in t.get_roots():
                print(f'Group:{str(r)}\n\t Tool:{str(t)}')
            
if __name__ == "__main__":
    asyncio.run(main())
