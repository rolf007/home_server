import asyncio

class Timer:
    def __init__(self, timeout, callback):
        self._timeout = timeout
        self._callback = callback
        self._task = asyncio.ensure_future(self._job())

    async def _job(self):
        await asyncio.sleep(self._timeout)
        await self._callback()
        self._task = asyncio.ensure_future(self._job())

    def cancel(self):
        self._task.cancel()

class Loop:
    def __init__(self, ittr):
        self.ittr = ittr.__iter__()
        self.stopped = False

        self._task = asyncio.ensure_future(self._job())

    def stop(self):
        self.stopped = True

    async def _job(self):
        if self.stopped:
            return
        try:
            i = self.ittr.__next__()
        except StopIteration:
            self.done()
            return
        try:
            await self.body(i)
        except Exception as e:
            print(e)
        self._task = asyncio.ensure_future(self._job())
