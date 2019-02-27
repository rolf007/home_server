#!/usr/bin/env python3

from aiohttp import web

async def handle(request):
    text = """
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link rel="apple-touch-icon" href='/assets/apple-touch-icon.png'/>
<script src="https://ajax.googleapis.com/ajax/libs/jquery/3.3.1/jquery.min.js"></script>

</head>
<body>

<iframe width="10" height="10" border="0" name="dummyframe" id="dummyframe"></iframe>
<!--<img src="/assets/apple-touch-icon.png"\>-->

<form action="http://192.168.0.100:5100/suresms" target="dummyframe">

  <input type="hidden" name="receivedutcdatetime" value="time" />
  <input type="hidden" name="receivedfromphonenumber" value="12345678" />
  <input type="hidden" name="receivedbyphonenumber" value="87654321" />
  <input type="hidden" name="body" value="pl svensk" />
  <button type="submit">Ulf Lundell & Bo Kasper</button>
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

<button onclick="myFunction()">Test1 (led)</button>
<button onclick="myFunction2()">Test1 (png)</button>

<script>
function myFunction() {
  $.get("http://127.0.0.1:5008/set", {anim:"boot"}, function(data, status){
    alert("Data: foo" + status);
  });
}
</script>
<script>
function myFunction2() {
  $.get("assets/apple-touch-icon.png", function(data, status){
    alert("Data: foo" + status);
  });
}
</script>
</body>
</html>
"""
    peername = request.transport.get_extra_info('peername')
    print(peername)

    headers = {'content-type': 'text/html'}
    return web.Response(headers=headers, text=text)

async def png(request):
    headers = {'content-type': 'image/png'}
    return web.FileResponse('./web_app/assets/apple-touch-icon.png')

app = web.Application()
app.add_routes([web.get('/', handle),
                web.get('/{name}', handle),
                web.get('/assets/apple-touch-icon.png', png)])

web.run_app(app)

