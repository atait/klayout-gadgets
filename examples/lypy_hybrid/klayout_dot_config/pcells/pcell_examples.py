from phidl import Device, Layer, geometry as pg

some_layer = Layer(1)

def some_device(width=10, height=20):
    D = Device('somedevice')
    r1 = D << pg.rectangle((width, height), layer=some_layer)
    r2 = D << pg.circle(radius=width, layer=some_layer)
    r2.movex(30)
    return D