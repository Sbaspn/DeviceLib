#!/usr/bin/env python3

from phidl import Device, Layer
import phidl.geometry as pg

def snspd(width=0.1, pitch=0.2, size=(10,10), trench=2, connector_width=None, turn_ratio=5, layer=1):
    D = Device('Pixel')
    if connector_width:
        W = pg.snspd_expanded(wire_width=width, wire_pitch=pitch, size=size, connector_width=connector_width, turn_ratio=turn_ratio, layer=layer)
    else:
        W = pg.snspd(wire_width=width, wire_pitch=pitch, size=size, turn_ratio=turn_ratio, layer=layer)
    snspd = D.add_ref(W)
    D.add_port(1, port=W.ports[1])
    D.add_port(2, port=W.ports[2])
    D.flatten()
    return D

def snspd_array(width=0.1, pitch=0.2, ch_width=1, size=(10,10), n=(4,4), negative=True, trench=0.25, turn_ratio=5, ch1_layer=1, ch2_layer=2, via_layer=3):
    D = Device()
    P = snspd(width, pitch, size, trench, turn_ratio=turn_ratio, layer=ch1_layer)

    L1 = Device('Layer1')
    wirepix = L1.add_ref(P)

    T = pg.tee(size=(ch_width, ch_width), stub_size=(width, trench), taper_type='fillet', layer=ch1_layer)
    tee1 = L1.add_ref(T)
    tee1.connect(3, wirepix.ports[1])
    R1 = pg.straight(size=(ch_width,size[1]+ch_width+trench), layer=ch1_layer)
    ch1ch = L1.add_ref(R1)
    ch1ch.connect(1, tee1.ports[2])
    tee2 = L1.add_ref(T)
    tee2.connect(3, wirepix.ports[2])
    teex, teey = tee2.xmax, tee2.ymax
    L1.add_port('L1N', port=tee1.ports[1])
    L1.add_port('L1S', port=ch1ch.ports[2])
    port_ = tee2.ports[2]
    if negative:
        L1 = pg.outline(L1, distance=trench, layer=ch1_layer, open_ports=trench)
    port_.orientation += 180
    L1.add_port('L2N', port=port_)
    lay1 = D.add_ref(L1)

    R2 = pg.rectangle(size=(ch_width*0.8, ch_width*0.8), layer=via_layer)
    via = D.add_ref(R2)
    via.move(origin=(via.xmax, via.ymax), destination=(teex, teey))
    via.move((-0.1*ch_width,-0.1*ch_width))

    L2 = Device('Layer2')
    R3 = pg.straight(size=(ch_width, ch_width), layer=ch2_layer)
    ch2via = L2.add_ref(R3)
    ch2via.connect(2, lay1.ports['L2N'])
    R4 = pg.compass(size=(ch_width,ch_width), layer=ch2_layer)
    ch2tee = L2.add_ref(R4)
    ch2tee.connect('N', ch2via.ports[1])
    R5 = pg.straight(size=(ch_width, size[0]+2*ch_width), layer=ch2_layer)
    ch2ch = L2.add_ref(R5)
    ch2ch.connect(2, ch2tee.ports['W'])
    R6 = pg.straight(size=(ch_width, trench), layer=ch2_layer)
    ch2cap = L2.add_ref(R6)
    ch2cap.connect(1, ch2tee.ports['E'])
    L2.add_port('L2E', port=ch2ch.ports[1])
    L2.add_port('L2W', port=ch2cap.ports[2])
    if negative:
        L2 = pg.outline(L2, distance=trench, layer=ch2_layer, open_ports=trench)
    lay2 = D.add_ref(L2)
    D.add_port('N', port=lay1.ports['L1N'])
    D.add_port('S', port=lay1.ports['L1S'])
    D.add_port('E', port=lay2.ports['L2E'])
    D.add_port('W', port=lay2.ports['L2W'])
    D.flatten()

    A = Device('Pixel_Array')
    arr = A.add_array(D, columns=n[0], rows=n[1], spacing=(D.xsize,D.ysize))
    for i in range(arr.columns):
        A.add_port(name='Col{}S'.format(i),
                   midpoint=(D.ports['S'].midpoint[0]+i*D.xsize, D.ports['S'].midpoint[1]),
                   width=ch_width, orientation=-90)
        A.add_port(name='Col{}N'.format(i),
                   midpoint=(D.ports['S'].midpoint[0]+i*D.xsize, D.ports['N'].midpoint[1]+(arr.rows-1)*D.ysize),
                   width=ch_width, orientation=90)
    for j in range(arr.rows):
        A.add_port(name='Row{}E'.format(j),
                   midpoint=(D.ports['E'].midpoint[0], D.ports['E'].midpoint[1]+j*D.ysize),
                   width=ch_width, orientation=180)
        A.add_port(name='Row{}W'.format(j),
                   midpoint=(D.ports['W'].midpoint[0]+(arr.columns-1)*D.xsize, D.ports['W'].midpoint[1]+j*D.ysize),
                   width=ch_width, orientation=0)
    return A
