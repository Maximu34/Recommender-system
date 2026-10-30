"""Upper-bound evaluation of query-by-humming.

Synthesizes a "perfect hum" from each track's own melody contour -- clean
pitch, no timbre, no human error -- and checks whether /hum retrieves that
track. This measures the *ceiling*: if the pipeline cannot find a track from
its own contour, no amount of good singing will help.

It does not replace the human study in the plan. Real hums are transposed,
rhythmically loose and timbrally nothing like a sine wave, so scores here
will always be optimistic. Use this to catch regressions and to size the
melody index; use recorded hums for the number that goes in the report.

The backend must already be running.

Usage:
    python -m scripts.eval_humming --n 20
"""
import argparse, io, json, sys, urllib.request, wave
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np
from app import config, store

ap = argparse.ArgumentParser()
ap.add_argument('--n', type=int, default=6, help='how many tracks to probe')
ap.add_argument('--api', default='http://127.0.0.1:8000')
ap.add_argument('--secs', type=float, default=6.0, help='hum length in seconds')
args = ap.parse_args()
API = args.api
mel={int(k):np.asarray(v,dtype=np.float32) for k,v in json.loads(config.MELODY_INDEX.read_text()).items()}
c=store.connect(); store.init_schema(c); T={t.id:t for t in store.all_tracks(c)}; c.close()

def synth(contour, sr=16000, secs=6.0):
    """Sine wave tracking the contour, as a clean stand-in for a hum."""
    n=int(secs*sr)
    ph=np.interp(np.linspace(0,len(contour)-1,n), np.arange(len(contour)), contour)
    f=220.0*(2.0**(ph/12.0))
    y=0.5*np.sin(2*np.pi*np.cumsum(f)/sr)
    # gentle fade so the edges don't confuse the pitch tracker
    e=int(0.05*sr); y[:e]*=np.linspace(0,1,e); y[-e:]*=np.linspace(1,0,e)
    return (y*32767).astype(np.int16)

def wav_bytes(pcm, sr=16000):
    b=io.BytesIO()
    with wave.open(b,'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(pcm.tobytes())
    return b.getvalue()

def post(data):
    boundary='----humtest'
    body=(f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="hum.wav"\r\n'
          'Content-Type: audio/wav\r\n\r\n').encode()+data+f'\r\n--{boundary}--\r\n'.encode()
    r=urllib.request.Request(API+'/hum?k=10', data=body,
        headers={'Content-Type':f'multipart/form-data; boundary={boundary}'})
    return json.load(urllib.request.urlopen(r, timeout=180))

targets=[t for t in list(mel)[:args.n]]
ranks=[]
for tid in targets:
    seg=mel[tid]
    start=len(seg)//3
    seg=seg[start:start+int(args.secs*config.MELODY_HZ)]   # from mid-clip
    if len(seg)<20: continue
    res=post(wav_bytes(synth(seg, secs=args.secs)))
    ids=[r['id'] for r in res['results']]
    rank=ids.index(tid)+1 if tid in ids else None
    ranks.append(rank)
    tt=T[tid]; vr=res['voiced_ratio']
    mark='OK ' if rank==1 else ('top10' if rank else 'MISS')
    print(f'{mark} rank={str(rank):>4s}  {tt.title[:32]:34s} voiced={vr:.2f}')
    if rank!=1:
        print(f'        got #1: {T[ids[0]].title[:40]}')
hit1=sum(1 for r in ranks if r==1); hit10=sum(1 for r in ranks if r)
print(f'\ntop-1: {hit1}/{len(ranks)}   top-10: {hit10}/{len(ranks)}')
