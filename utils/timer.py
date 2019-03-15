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

    def start(self, asynch=True):
        if asynch:
            self._task = asyncio.ensure_future(self._job())
        else:
            self._job2()

    def stop(self):
        self.stopped = True

    async def foo(self, x):
        self.body(x)

    def _job2(self):
        if self.stopped:
            return
        try:
            i = self.ittr.__next__()
            print(i)
        except StopIteration:
            print("done")
            self.done()
            return
        try:
            self.body(i)
        except Exception as e:
            print(e)
        self._job2()

    async def _job(self):
        if self.stopped:
            return
        try:
            i = self.ittr.__next__()
        except StopIteration:
            self.done()
            return
        try:
            await self.foo(i)
        except Exception as e:
            print(e)
        self._task = asyncio.ensure_future(self._job())
