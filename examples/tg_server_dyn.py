from toolgroups import Group, ToolConverter, ToolgroupMCPServer
from mcp.types import ToolAnnotations

# Create server
tg_server = ToolgroupMCPServer("toolgroup server")

def op1():
    '''my operation one'''
    print("op1 called")
    
def op2():
    '''my operation two'''
    print("op2 called")
    
untrusted_group=Group(name="untrusted",title="Untrusted Tools Group", description="The tools in this group are not to be trusted")

tg_server.add_tool(op1, 
                   title="Untrusted Operation1", 
                   parent=untrusted_group,
                   annotations=ToolAnnotations(read_only_hint=False))

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
