import itertools
import quad_2m70 as q
lam2, lam7 = 299.79/145, 299.79/436
def score(ev, z0):
    import necsim
    fb = min(e['fb'] for e in ev); g = min(e['g'] for e in ev)
    swr = max(necsim.roe(complex(*e['z']), z0) for e in ev)
    return fb + 2*g - 4*max(0, swr-1.5), fb, g, swr
best2=None
for rs, sp, ds in itertools.product([1.03,1.05,1.07,1.09], [0.15,0.18,0.2,0.22,0.25], [0.99,1.0,1.01,1.02]):
    c=q.base('opt2'); s2=q.P(145)/4
    c['r2']=s2*ds*rs; c['d2']=s2*ds; c['x_d2']=sp*lam2; c['x_d7']=c['x_d2']; c['x_r7']=c['x_d2']-0.2*lam7
    ev=q.evaluar(c,'2m',(144.0,146.0,3))
    for z0 in (50,):
        sc=score(ev,z0)
        if not best2 or sc[0]>best2[0]: best2=(sc[0],sc,rs,sp,ds,[ (e['f'],e['z']) for e in ev])
print('2m', best2)
best7=None
for rs, sp, ds, dirs, dirp in itertools.product([1.03,1.05,1.07,1.09],[0.12,0.15,0.18,0.2,0.25],[0.99,1.0,1.02,1.04,1.06],[None,0.93,0.95,0.97],[0.1,0.15,0.2]):
    if dirs is None and dirp!=0.1: continue
    c=q.base('opt7'); s7=q.P(436)/4
    c['r7']=s7*ds*rs; c['d7']=s7*ds; c['x_r7']=c['x_d2']-sp*lam7
    if dirs: c['dir7']=[(c['x_d2']+dirp*lam7, s7*ds*dirs)]
    ev=q.evaluar(c,'70',(430.0,440.0,3))
    sc=score(ev,50)
    if not best7 or sc[0]>best7[0]: best7=(sc[0],sc,rs,sp,ds,dirs,dirp,[(e['f'],e['z']) for e in ev])
print('70', best7)
