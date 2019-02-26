#!/usr/bin/env python3

from aiohttp import web

async def handle(request):
    text = """
<iframe width="10" height="10" border="0" name="dummyframe" id="dummyframe"></iframe>

<form action="http://192.168.0.100:5100/suresms" target="dummyframe">

  <input type="hidden" name="receivedutcdatetime" value="time" />
  <input type="hidden" name="receivedfromphonenumber" value="12345678" />
  <input type="hidden" name="receivedbyphonenumber" value="87654321" />
  <input type="hidden" name="body" value="p .r ulf lundell" />
  <button type="submit">Ulf Lundell</button>
</form>

<form action="http://192.168.0.100:5100/suresms" target="dummyframe">

  <input type="hidden" name="receivedutcdatetime" value="time" />
  <input type="hidden" name="receivedfromphonenumber" value="12345678" />
  <input type="hidden" name="receivedbyphonenumber" value="87654321" />
  <input type="hidden" name="body" value="radio p1" />
  <button type="submit">P1</button>
</form>

<form action="http://192.168.0.100:5100/suresms" target="dummyframe">

  <input type="hidden" name="receivedutcdatetime" value="time" />
  <input type="hidden" name="receivedfromphonenumber" value="12345678" />
  <input type="hidden" name="receivedbyphonenumber" value="87654321" />
  <input type="hidden" name="body" value="radio p2" />
  <button type="submit">P2</button>
</form>

<form action="http://192.168.0.100:5100/suresms" target="dummyframe">
  <input type="hidden" name="receivedutcdatetime" value="time" />
  <input type="hidden" name="receivedfromphonenumber" value="12345678" />
  <input type="hidden" name="receivedbyphonenumber" value="87654321" />
  <input type="hidden" name="body" value="radio p3" />
  <button type="submit">P3</button>
</form>

<form action="http://192.168.0.100:5100/suresms" target="dummyframe">
  <input type="hidden" name="receivedutcdatetime" value="time" />
  <input type="hidden" name="receivedfromphonenumber" value="12345678" />
  <input type="hidden" name="receivedbyphonenumber" value="87654321" />
  <input type="hidden" name="body" value="radio 24syv" />
  <button type="submit">24syv</button>
</form>

<form action="http://192.168.0.100:5100/suresms" target="dummyframe">
  <input type="hidden" name="receivedutcdatetime" value="time" />
  <input type="hidden" name="receivedfromphonenumber" value="12345678" />
  <input type="hidden" name="receivedbyphonenumber" value="87654321" />
  <input type="hidden" name="body" value="stop" />
  <button type="submit">Stop</button>
</form>

"""
    headers = {'content-type': 'text/html'}
    return web.Response(headers=headers, text=text)

app = web.Application()
app.add_routes([web.get('/', handle),
                web.get('/{name}', handle)])

web.run_app(app)

