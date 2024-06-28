import asyncio
import mse1

s = mse1.sdlCommunicator('test')

asyncio.run(s.subsystem_main())