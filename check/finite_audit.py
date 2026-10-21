"""Finite manuscript arithmetic only: sixteen witnesses, seeds and one upper bound.

No interval enumeration, production rebuild, or campaign execution.
Uses Python integers, exhaustive trial division, Fraction and math.isqrt.
"""
from pathlib import Path
from fractions import Fraction
from functools import reduce, lru_cache
import hashlib
import json
import math
import platform

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent

def need(ok, message):
    if not ok:
        raise ValueError(message)

@lru_cache(None)
def factors(n):
    need(n >= 0, 'negative operand')
    remaining, p, result = n, 2, []
    while remaining > 1 and p <= remaining // p:
        e = 0
        while remaining % p == 0:
            remaining //= p
            e += 1
        if e:
            result.append((p, e))
        p = 3 if p == 2 else p + 2
    if remaining > 1:
        result.append((remaining, 1))
    if n >= 1:
        need(math.prod(p**e for p, e in result) == n, 'factor reconstruction')
    return tuple(result)

def derivative(n):
    return sum(e*(n//p) for p, e in factors(n)) if n >= 2 else 0

def square(n):
    r = math.isqrt(n)
    return r if r*r == n else None

def chain(n, depth=8):
    values = [n]
    for _ in range(depth):
        values.append(derivative(values[-1]))
    return values

def main():
    raw = (ROOT/'data/a249107.txt').read_bytes()
    braw = (ROOT/'data/b249107.txt').read_bytes()
    need(raw.endswith(b'\n\n') and not raw.endswith(b'\n\n\n'), 'a framing')
    need(braw.endswith(b'\n\n') and not braw.endswith(b'\n\n\n'), 'b framing')
    rows = [tuple(map(int, s.split())) for s in raw.splitlines()
            if s and not s.startswith(b'#')]
    b = [tuple(map(int, s.split())) for s in braw.splitlines() if s]
    need([r[:2] for r in rows] == b and [r[0] for r in rows] == list(range(1,17)), 'index join')
    forms, observations = {}, []
    for i, *w in rows:
        need(len(w) == 7 and chain(w[0],5) == w[:6], f'derivative chain {i}')
        need(sum(x*x for x in w[:6]) == w[-1]**2 and w[-1] > 0, f'square {i}')
        g = reduce(math.gcd, w)
        f = tuple(x//g for x in w)
        lam = Fraction(f[1]-derivative(f[0]), f[0])
        need(lam == Fraction(derivative(g),g), f'rate {i}')
        need(all(Fraction(derivative(f[j]))+lam*f[j] == f[j+1] for j in range(5)), f'transitions {i}')
        need(sum(x*x for x in f[:6]) == f[-1]**2 and reduce(math.gcd,f)==1, f'primitive square {i}')
        form = forms.setdefault(f, {'coordinates':f,'lambda':str(lam),'indices':[],'scales':[]})
        form['indices'].append(i); form['scales'].append(g)
        c = chain(w[0])
        roots = {str(h): square(sum(x*x for x in c[:h+1])) for h in range(1,9)}
        observations.append({'index':i,'witness':w,'gcd':g,'form':f,'lambda':str(lam),
                             'factors_n':factors(w[0]),'gcd_n_Dn':math.gcd(w[0],w[1]),
                             'chain_to_depth8':c,'square_roots_by_depth':roots})
        observation=observations[-1]
        zero=next((j for j,x in enumerate(c) if x==0),None)
        certificates=[(j,p,x) for j,x in enumerate(c) if x>1
                      for p,e in factors(x) if e>=p and x>p**p]
        need(zero is not None or certificates, f'dynamics certificate {i}')
        observation['dynamics']=({'kind':'terminates','first_zero':zero} if zero is not None
                                 else {'kind':'diverges','certificate':certificates[0]})
    seeds=[]
    for form in forms.values():
        f=form['coordinates'];lam=Fraction(form['lambda']);B=lam.denominator;A=lam.numerator
        bf=factors(B);need(all(e==1 for p,e in bf),'squarefree rate denominator')
        residues=[(p, A*pow(B//p,-1,p)%p) for p,e in bf]
        core=math.prod(p**c for p,c in residues)
        alpha=sum((Fraction(c,p) for p,c in residues),Fraction(0))
        k=lam-alpha;need(k.denominator==1 and k>=0,'scale count')
        form.update(residue_core=core,k=int(k))
        if lam:
            seeds.append({'form':f,'lambda':str(lam),'D_coordinates':[derivative(x) for x in f[:5]]})
    need(len(forms)==11,'form count')
    upper_n=2434337*3**3*5**5
    upper=chain(upper_n,5);r=square(sum(x*x for x in upper));need(r is not None,'upper witness')
    upper.append(r)
    need(upper_n>rows[-1][1],'upper ordering')
    u=[40000000000000]
    for _ in range(5):u.append(u[-1]*(u[-1].bit_length()-1)//2)
    q=sum(x*x for x in u)
    result={'status':'PASS','scope':__doc__,'python':platform.python_version(),
            'a_sha256':hashlib.sha256(raw).hexdigest(),'b_sha256':hashlib.sha256(braw).hexdigest(),
            'rows':observations,'forms':list(forms.values()),'seeds':seeds,
            'upper_witness':upper,'cap_bounds':u,'Q_bound':q,'Q_bits':q.bit_length(),
            'root_bound':math.isqrt(q),'derivative_identities':80,'square_identities':16,
            'extra_depth_identities':48,'distinct_factor_operands':factors.cache_info().currsize,
            'n4_depth_example':{'Q3':sum(x*x for x in chain(4,3)),
                                'Q5':sum(x*x for x in chain(4,5))}}
    (OUT/'finite_audit.json').write_text(json.dumps(result,indent=2)+'\n')
    print('PASS: 16 witnesses, 80 derivative and 16 square identities, 11 primitive forms, 48 depth6..8 transitions.')
    for row in observations:
        print(row['index'],row['gcd'],row['factors_n'],row['chain_to_depth8'][6:],
              {h:r for h,r in row['square_roots_by_depth'].items() if r is not None})
    print('Seeds:',seeds);print('upper:',upper);print('cap:',u,q,q.bit_length(),math.isqrt(q))

if __name__=='__main__':
    main()
