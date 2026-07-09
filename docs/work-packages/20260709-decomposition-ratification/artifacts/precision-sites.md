# Double-Precision Sites (mechanical)

Evidence mode: Ran.
Pattern: `double precision` | `real*8` | `dble(` | `D`-exponent literal.

| Unit | Line | Source (truncated) |
|---|---|---|
| `blockdata` | 1073 | `data g_dsum/108*0.d0/` |
| `blockdata` | 1074 | `data g_ssum/108*0.d0/` |
| `dstg` | 1696 | `double precision fu,xx` |
| `confls` | 4659 | `double precision bound,df,p,q,x` |
| `confls` | 4662 | `x = dble(x2sum)` |
| `confls` | 4663 | `df = dble(n)` |
| `cdfchi` | 4787 | `DOUBLE PRECISION tol` |
| `cdfchi` | 4788 | `PARAMETER (tol=1.0D-8)` |
| `cdfchi` | 4789 | `DOUBLE PRECISION atol` |
| `cdfchi` | 4790 | `PARAMETER (atol=1.0D-50)` |
| `cdfchi` | 4791 | `DOUBLE PRECISION zero,inf` |
| `cdfchi` | 4792 | `PARAMETER (zero=1.0D-100,inf=1.0D100)` |
| `cdfchi` | 4795 | `DOUBLE PRECISION bound,df,p,q,x` |
| `cdfchi` | 4799 | `DOUBLE PRECISION ccum,cum,fx,porq,pq` |
| `cdfchi` | 4803 | `DOUBLE PRECISION spmpar` |
| `cdfchi` | 4814 | `data porq/0.d0/` |
| `cdfchi` | 4817 | `bound = 1.0D0` |
| `cdfchi` | 4820 | `10 bound = 3.0D0` |
| `cdfchi` | 4825 | `IF (.NOT. ((p.LT.0.0D0).OR. (p.GT.1.0D0))) GO TO 60` |
| `cdfchi` | 4826 | `IF (.NOT. (p.LT.0.0D0)) GO TO 40` |
| `cdfchi` | 4827 | `bound = 0.0D0` |
| `cdfchi` | 4830 | `40 bound = 1.0D0` |
| `cdfchi` | 4836 | `IF (.NOT. ((q.LE.0.0D0).OR. (q.GT.1.0D0))) GO TO 100` |
| `cdfchi` | 4837 | `IF (.NOT. (q.LE.0.0D0)) GO TO 80` |
| `cdfchi` | 4838 | `bound = 0.0D0` |
| `cdfchi` | 4841 | `80 bound = 1.0D0` |
| `cdfchi` | 4847 | `IF (.NOT. (x.LT.0.0D0)) GO TO 120` |
| `cdfchi` | 4848 | `bound = 0.0D0` |
| `cdfchi` | 4854 | `IF (.NOT. (df.LE.0.0D0)) GO TO 140` |
| `cdfchi` | 4855 | `bound = 0.0D0` |
| `cdfchi` | 4862 | `IF (.NOT. (abs(((pq)-0.5D0)-0.5D0).GT.` |
| `cdfchi` | 4863 | `+    (3.0D0*spmpar(1)))) GO TO 180` |
| `cdfchi` | 4864 | `IF (.NOT. (pq.LT.0.0D0)) GO TO 160` |
| `cdfchi` | 4865 | `bound = 0.0D0` |
| `cdfchi` | 4868 | `160 bound = 1.0D0` |
| `cdfchi` | 4884 | `IF (porq.GT.1.5D0) THEN` |
| `cdfchi` | 4891 | `x = 5.0D0` |
| `cdfchi` | 4892 | `CALL dstinv(0.0D0,inf,0.5D0,0.5D0,5.0D0,atol,tol)` |
| `cdfchi` | 4902 | `250     IF (.NOT. ((fx+porq).GT.1.5D0)) GO TO 260` |
| `cdfchi` | 4912 | `bound = 0.0D0` |
| `cdfchi` | 4921 | `df = 5.0D0` |
| `cdfchi` | 4922 | `CALL dstinv(zero,inf,0.5D0,0.5D0,5.0D0,atol,tol)` |
| `cdfchi` | 4932 | `330     IF (.NOT. ((fx+porq).GT.1.5D0)) GO TO 340` |
| `cumchi` | 4992 | `DOUBLE PRECISION df,x,cum,ccum` |
| `cumchi` | 4995 | `DOUBLE PRECISION a,xx` |
| `cumchi` | 5001 | `a = df*0.5D0` |
| `cumchi` | 5002 | `xx = x*0.5D0` |
| `cumgam` | 5051 | `DOUBLE PRECISION a,x,cum,ccum` |
| `cumgam` | 5057 | `IF (.NOT. (x.LE.0.0D0)) GO TO 10` |
| `cumgam` | 5058 | `cum = 0.0D0` |
| `cumgam` | 5059 | `ccum = 1.0D0` |
| `dinvr` | 5129 | `DOUBLE PRECISION fx,x,zabsst,zabsto,zbig,zrelst,zrelto,zsmall,` |
| `dinvr` | 5135 | `DOUBLE PRECISION absstp,abstol,big,fbig,fsmall,relstp,reltol,` |
| `dinvr` | 5180 | `IF (fsmall.LE.0.0D0) GO TO 30` |
| `dinvr` | 5186 | `30 IF (fbig.GE.0.0D0) GO TO 40` |
| `dinvr` | 5194 | `50 IF (fsmall.GE.0.0D0) GO TO 60` |
| `dinvr` | 5200 | `60 IF (fbig.LE.0.0D0) GO TO 70` |
| `dinvr` | 5215 | `IF (.NOT. (yy.EQ.0.0D0)) GO TO 100` |
| `dinvr` | 5220 | `100 qup = (qincr .AND. (yy.LT.0.0D0)) .OR.` |
| `dinvr` | 5221 | `+      (.NOT.qincr .AND. (yy.GT.0.0D0))` |
| `dinvr` | 5240 | `qbdd = (qincr .AND. (yy.GE.0.0D0)) .OR.` |
| `dinvr` | 5241 | `+       (.NOT.qincr .AND. (yy.LE.0.0D0))` |
| `dinvr` | 5275 | `qbdd = (qincr .AND. (yy.LE.0.0D0)) .OR.` |
| `dinvr` | 5276 | `+       (.NOT.qincr .AND. (yy.GE.0.0D0))` |
| `dzror` | 5480 | `DOUBLE PRECISION fx,x,xhi,xlo,zabstl,zreltl,zxhi,zxlo` |
| `dzror` | 5488 | `DOUBLE PRECISION a,abstol,b,c,d,fa,fb,fc,fd,fda,fdb,m,mb,p,q,` |
| `dzror` | 5497 | `DOUBLE PRECISION ftol` |
| `dzror` | 5500 | `ftol(zx) = 0.5D0*max(abstol,reltol*abs(zx))` |
| `dzror` | 5524 | `20 IF (.NOT. (fb.LT.0.0D0)) GO TO 40` |
| `dzror` | 5525 | `IF (.NOT. (fx.LT.0.0D0)) GO TO 30` |
| `dzror` | 5532 | `40 IF (.NOT. (fb.GT.0.0D0)) GO TO 60` |
| `dzror` | 5533 | `IF (.NOT. (fx.GT.0.0D0)) GO TO 50` |
| `dzror` | 5558 | `m = (c+b)*.5D0` |
| `dzror` | 5576 | `130 IF (.NOT. (p.LT.0.0D0)) GO TO 140` |
| `dzror` | 5579 | `140 IF (ext.EQ.3) p = p*2.0D0` |
| `dzror` | 5580 | `IF (.NOT. ((p*1.0D0).EQ.0.0D0.OR.p.LE. (q*tol))) GO TO 150` |
| `dzror` | 5603 | `IF (.NOT. ((fc*fb).GE.0.0D0)) GO TO 210` |
| `dzror` | 5614 | `qrzero = (fc.GE.0.0D0 .AND. fb.LE.0.0D0) .OR.` |
| `dzror` | 5615 | `+         (fc.LT.0.0D0 .AND. fb.GE.0.0D0)` |
| `erf` | 5703 | `DOUBLE PRECISION FUNCTION erf(x)` |
| `erf` | 5708 | `DOUBLE PRECISION x` |
| `erf` | 5711 | `DOUBLE PRECISION ax,bot,c,t,top,x2` |
| `erf` | 5714 | `DOUBLE PRECISION a(5),b(3),p(8),q(8),r(5),s(4)` |
| `erf` | 5724 | `DATA c/.564189583547756D0/` |
| `erf` | 5725 | `DATA a(1)/.771058495001320D-04/,a(2)/-.133733772997339D-02/,` |
| `erf` | 5726 | `+     a(3)/.323076579225834D-01/,a(4)/.479137145607681D-01/,` |
| `erf` | 5727 | `+     a(5)/.128379167095513D+00/` |
| `erf` | 5728 | `DATA b(1)/.301048631703895D-02/,b(2)/.538971687740286D-01/,` |
| `erf` | 5729 | `+     b(3)/.375795757275549D+00/` |
| `erf` | 5730 | `DATA p(1)/-1.36864857382717D-07/,p(2)/5.64195517478974D-01/,` |
| `erf` | 5731 | `+     p(3)/7.21175825088309D+00/,p(4)/4.31622272220567D+01/,` |
| `erf` | 5732 | `+     p(5)/1.52989285046940D+02/,p(6)/3.39320816734344D+02/,` |
| `erf` | 5733 | `+     p(7)/4.51918953711873D+02/,p(8)/3.00459261020162D+02/` |
| `erf` | 5734 | `DATA q(1)/1.00000000000000D+00/,q(2)/1.27827273196294D+01/,` |
| `erf` | 5735 | `+     q(3)/7.70001529352295D+01/,q(4)/2.77585444743988D+02/,` |
| `erf` | 5736 | `+     q(5)/6.38980264465631D+02/,q(6)/9.31354094850610D+02/,` |
| `erf` | 5737 | `+     q(7)/7.90950925327898D+02/,q(8)/3.00459260956983D+02/` |
| `erf` | 5738 | `DATA r(1)/2.10144126479064D+00/,r(2)/2.62370141675169D+01/,` |
| `erf` | 5739 | `+     r(3)/2.13688200555087D+01/,r(4)/4.65807828718470D+00/,` |
| `erf` | 5740 | `+     r(5)/2.82094791773523D-01/` |
| `erf` | 5741 | `DATA s(1)/9.41537750555460D+01/,s(2)/1.87114811799590D+02/,` |
| `erf` | 5742 | `+     s(3)/9.90191814623914D+01/,s(4)/1.80124575948747D+01/` |
| `erf` | 5747 | `IF (ax.GT.0.5D0) GO TO 10` |
| `erf` | 5749 | `top = ((((a(1)*t+a(2))*t+a(3))*t+a(4))*t+a(5)) + 1.0D0` |
| `erf` | 5750 | `bot = ((b(1)*t+b(2))*t+b(3))*t + 1.0D0` |
| `erf` | 5754 | `10 IF (ax.GT.4.0D0) GO TO 20` |
| `erf` | 5759 | `erf = 0.5D0 + (0.5D0-exp(-x*x)*top/bot)` |
| `erf` | 5760 | `IF (x.LT.0.0D0) erf = -erf` |
| `erf` | 5763 | `20 IF (ax.GE.5.8D0) GO TO 30` |
| `erf` | 5765 | `t = 1.0D0/x2` |
| `erf` | 5767 | `bot = (((s(1)*t+s(2))*t+s(3))*t+s(4))*t + 1.0D0` |
| `erf` | 5769 | `erf = 0.5D0 + (0.5D0-exp(-x2)*erf)` |
| `erf` | 5770 | `IF (x.LT.0.0D0) erf = -erf` |
| `erf` | 5773 | `30 erf = sign(1.0D0,x)` |
| `erfc1` | 5778 | `DOUBLE PRECISION FUNCTION erfc1(ind,x)` |
| `erfc1` | 5786 | `DOUBLE PRECISION x` |
| `erfc1` | 5790 | `DOUBLE PRECISION ax,bot,c,e,t,top,w` |
| `erfc1` | 5793 | `DOUBLE PRECISION a(5),b(3),p(8),q(8),r(5),s(4)` |
| `erfc1` | 5796 | `DOUBLE PRECISION exparg` |
| `erfc1` | 5807 | `DATA c/.564189583547756D0/` |
| `erfc1` | 5808 | `DATA a(1)/.771058495001320D-04/,a(2)/-.133733772997339D-02/,` |
| `erfc1` | 5809 | `+     a(3)/.323076579225834D-01/,a(4)/.479137145607681D-01/,` |
| `erfc1` | 5810 | `+     a(5)/.128379167095513D+00/` |
| `erfc1` | 5811 | `DATA b(1)/.301048631703895D-02/,b(2)/.538971687740286D-01/,` |
| `erfc1` | 5812 | `+     b(3)/.375795757275549D+00/` |
| `erfc1` | 5813 | `DATA p(1)/-1.36864857382717D-07/,p(2)/5.64195517478974D-01/,` |
| `erfc1` | 5814 | `+     p(3)/7.21175825088309D+00/,p(4)/4.31622272220567D+01/,` |
| `erfc1` | 5815 | `+     p(5)/1.52989285046940D+02/,p(6)/3.39320816734344D+02/,` |
| `erfc1` | 5816 | `+     p(7)/4.51918953711873D+02/,p(8)/3.00459261020162D+02/` |
| `erfc1` | 5817 | `DATA q(1)/1.00000000000000D+00/,q(2)/1.27827273196294D+01/,` |
| `erfc1` | 5818 | `+     q(3)/7.70001529352295D+01/,q(4)/2.77585444743988D+02/,` |
| `erfc1` | 5819 | `+     q(5)/6.38980264465631D+02/,q(6)/9.31354094850610D+02/,` |
| `erfc1` | 5820 | `+     q(7)/7.90950925327898D+02/,q(8)/3.00459260956983D+02/` |
| `erfc1` | 5821 | `DATA r(1)/2.10144126479064D+00/,r(2)/2.62370141675169D+01/,` |
| `erfc1` | 5822 | `+     r(3)/2.13688200555087D+01/,r(4)/4.65807828718470D+00/,` |
| `erfc1` | 5823 | `+     r(5)/2.82094791773523D-01/` |
| `erfc1` | 5824 | `DATA s(1)/9.41537750555460D+01/,s(2)/1.87114811799590D+02/,` |
| `erfc1` | 5825 | `+     s(3)/9.90191814623914D+01/,s(4)/1.80124575948747D+01/` |
| `erfc1` | 5833 | `IF (ax.GT.0.5D0) GO TO 10` |
| `erfc1` | 5835 | `top = ((((a(1)*t+a(2))*t+a(3))*t+a(4))*t+a(5)) + 1.0D0` |
| `erfc1` | 5836 | `bot = ((b(1)*t+b(2))*t+b(3))*t + 1.0D0` |
| `erfc1` | 5837 | `erfc1 = 0.5D0 + (0.5D0-x* (top/bot))` |
| `erfc1` | 5843 | `10 IF (ax.GT.4.0D0) GO TO 20` |
| `erfc1` | 5853 | `20 IF (x.LE.-5.6D0) GO TO 60` |
| `erfc1` | 5855 | `IF (x.GT.100.0D0) GO TO 70` |
| `erfc1` | 5858 | `30 t = (1.0D0/x)**2` |
| `erfc1` | 5860 | `bot = (((s(1)*t+s(2))*t+s(3))*t+s(4))*t + 1.0D0` |
| `erfc1` | 5866 | `IF (x.LT.0.0D0) erfc1 = 2.0D0*exp(x*x) - erfc1` |
| `erfc1` | 5869 | `50 w = dble(x)*dble(x)` |
| `erfc1` | 5871 | `e = w - dble(t)` |
| `erfc1` | 5872 | `erfc1 = ((0.5D0+ (0.5D0-e))*exp(-t))*erfc1` |
| `erfc1` | 5873 | `IF (x.LT.0.0D0) erfc1 = 2.0D0 - erfc1` |
| `erfc1` | 5878 | `60 erfc1 = 2.0D0` |
| `erfc1` | 5879 | `IF (ind.NE.0) erfc1 = 2.0D0*exp(x*x)` |
| `erfc1` | 5885 | `70 erfc1 = 0.0D0` |
| `exparg` | 5890 | `DOUBLE PRECISION FUNCTION exparg(l)` |
| `exparg` | 5904 | `DOUBLE PRECISION lnb` |
| `exparg` | 5918 | `lnb = .69314718055995D0` |
| `exparg` | 5922 | `lnb = 2.0794415416798D0` |
| `exparg` | 5926 | `lnb = 2.7725887222398D0` |
| `exparg` | 5929 | `30 lnb = dlog(dble(b))` |
| `exparg` | 5933 | `exparg = 0.99999D0* (m*lnb)` |
| `exparg` | 5937 | `exparg = 0.99999D0* (m*lnb)` |
| `gam1` | 5942 | `DOUBLE PRECISION FUNCTION gam1(a)` |
| `gam1` | 5947 | `DOUBLE PRECISION a` |
| `gam1` | 5950 | `DOUBLE PRECISION bot,d,s1,s2,t,top,w` |
| `gam1` | 5953 | `DOUBLE PRECISION p(7),q(5),r(9)` |
| `gam1` | 5960 | `DATA p(1)/.577215664901533D+00/,p(2)/-.409078193005776D+00/,` |
| `gam1` | 5961 | `+     p(3)/-.230975380857675D+00/,p(4)/.597275330452234D-01/,` |
| `gam1` | 5962 | `+     p(5)/.766968181649490D-02/,p(6)/-.514889771323592D-02/,` |
| `gam1` | 5963 | `+     p(7)/.589597428611429D-03/` |
| `gam1` | 5964 | `DATA q(1)/.100000000000000D+01/,q(2)/.427569613095214D+00/,` |
| `gam1` | 5965 | `+     q(3)/.158451672430138D+00/,q(4)/.261132021441447D-01/,` |
| `gam1` | 5966 | `+     q(5)/.423244297896961D-02/` |
| `gam1` | 5967 | `DATA r(1)/-.422784335098468D+00/,r(2)/-.771330383816272D+00/,` |
| `gam1` | 5968 | `+     r(3)/-.244757765222226D+00/,r(4)/.118378989872749D+00/,` |
| `gam1` | 5969 | `+     r(5)/.930357293360349D-03/,r(6)/-.118290993445146D-01/,` |
| `gam1` | 5970 | `+     r(7)/.223047661158249D-02/,r(8)/.266505979058923D-03/,` |
| `gam1` | 5971 | `+     r(9)/-.132674909766242D-03/` |
| `gam1` | 5972 | `DATA s1/.273076135303957D+00/,s2/.559398236957378D-01/` |
| `gam1` | 5977 | `d = a - 0.5D0` |
| `gam1` | 5978 | `IF (d.GT.0.0D0) t = d - 0.5D0` |
| `gam1` | 5981 | `10 gam1 = 0.0D0` |
| `gam1` | 5985 | `bot = (((q(5)*t+q(4))*t+q(3))*t+q(2))*t + 1.0D0` |
| `gam1` | 5987 | `IF (d.GT.0.0D0) GO TO 30` |
| `gam1` | 5991 | `30 gam1 = (t/a)* ((w-0.5D0)-0.5D0)` |
| `gam1` | 5996 | `bot = (s2*t+s1)*t + 1.0D0` |
| `gam1` | 5998 | `IF (d.GT.0.0D0) GO TO 50` |
| `gam1` | 5999 | `gam1 = a* ((w+0.5D0)+0.5D0)` |
| `gamma` | 6007 | `DOUBLE PRECISION FUNCTION gamma(a)` |
| `gamma` | 6023 | `DOUBLE PRECISION a` |
| `gamma` | 6026 | `DOUBLE PRECISION bot,d,g,lnx,pi,r1,r2,r3,r4,r5,s,t,top,w,x,z` |
| `gamma` | 6030 | `DOUBLE PRECISION p(7),q(7)` |
| `gamma` | 6033 | `DOUBLE PRECISION exparg,spmpar` |
| `gamma` | 6045 | `DATA pi/3.1415926535898D0/` |
| `gamma` | 6046 | `DATA d/.41893853320467274178D0/` |
| `gamma` | 6047 | `DATA p(1)/.539637273585445D-03/,p(2)/.261939260042690D-02/,` |
| `gamma` | 6048 | `+     p(3)/.204493667594920D-01/,p(4)/.730981088720487D-01/,` |
| `gamma` | 6049 | `+     p(5)/.279648642639792D+00/,p(6)/.553413866010467D+00/,` |
| `gamma` | 6050 | `+     p(7)/1.0D0/` |
| `gamma` | 6051 | `DATA q(1)/-.832979206704073D-03/,q(2)/.470059485860584D-02/,` |
| `gamma` | 6052 | `+     q(3)/.225211131035340D-01/,q(4)/-.170458969313360D+00/,` |
| `gamma` | 6053 | `+     q(5)/-.567902761974940D-01/,q(6)/.113062953091122D+01/,` |
| `gamma` | 6054 | `+     q(7)/1.0D0/` |
| `gamma` | 6055 | `DATA r1/.820756370353826D-03/,r2/-.595156336428591D-03/,` |
| `gamma` | 6056 | `+     r3/.793650663183693D-03/,r4/-.277777777770481D-02/,` |
| `gamma` | 6057 | `+     r5/.833333333333333D-01/` |
| `gamma` | 6061 | `gamma = 0.0D0` |
| `gamma` | 6063 | `IF (abs(a).GE.15.0D0) GO TO 110` |
| `gamma` | 6067 | `t = 1.0D0` |
| `gamma` | 6074 | `x = x - 1.0D0` |
| `gamma` | 6077 | `30 x = x - 1.0D0` |
| `gamma` | 6083 | `IF (a.GT.0.0D0) GO TO 70` |
| `gamma` | 6087 | `x = x + 1.0D0` |
| `gamma` | 6090 | `60 x = (x+0.5D0) + 0.5D0` |
| `gamma` | 6092 | `IF (t.EQ.0.0D0) RETURN` |
| `gamma` | 6099 | `IF (abs(t).GE.1.D-30) GO TO 80` |
| `gamma` | 6100 | `IF (abs(t)*spmpar(3).LE.1.0001D0) RETURN` |
| `gamma` | 6101 | `gamma = 1.0D0/t` |
| `gamma` | 6116 | `IF (a.LT.1.0D0) GO TO 100` |
| `gamma` | 6125 | `110 IF (abs(a).GE.1.D3) RETURN` |
| `gamma` | 6126 | `IF (a.GT.0.0D0) GO TO 120` |
| `gamma` | 6130 | `IF (t.GT.0.9D0) t = 1.0D0 - t` |
| `gamma` | 6133 | `IF (s.EQ.0.0D0) RETURN` |
| `gamma` | 6137 | `120 t = 1.0D0/ (x*x)` |
| `gamma` | 6148 | `g = (d+g) + (z-0.5D0)* (lnx-1.D0)` |
| `gamma` | 6150 | `t = g - dble(w)` |
| `gamma` | 6151 | `IF (w.GT.0.99999D0*exparg(0)) RETURN` |
| `gamma` | 6152 | `gamma = exp(w)* (1.0D0+t)` |
| `gamma` | 6153 | `IF (a.LT.0.0D0) gamma = (1.0D0/ (gamma*s))/x` |
| `gratio` | 6187 | `DOUBLE PRECISION a,ans,qans,x` |
| `gratio` | 6191 | `DOUBLE PRECISION a2n,a2nm1,acc,alog10,am0,amn,an,an0,apn,b2n,` |
| `gratio` | 6198 | `DOUBLE PRECISION acc0(3),big(3),d0(13),d1(12),d2(10),d3(8),d4(6),` |
| `gratio` | 6202 | `DOUBLE PRECISION erf,erfc1,gam1,gamma,rexp,rlog,spmpar` |
| `gratio` | 6223 | `DATA acc0(1)/5.D-15/,acc0(2)/5.D-7/,acc0(3)/5.D-4/` |
| `gratio` | 6224 | `DATA big(1)/20.0D0/,big(2)/14.0D0/,big(3)/10.0D0/` |
| `gratio` | 6225 | `DATA e00(1)/.25D-3/,e00(2)/.25D-1/,e00(3)/.14D0/` |
| `gratio` | 6226 | `DATA x00(1)/31.0D0/,x00(2)/17.0D0/,x00(3)/9.7D0/` |
| `gratio` | 6227 | `DATA alog10/2.30258509299405D0/` |
| `gratio` | 6228 | `DATA rt2pin/.398942280401433D0/` |
| `gratio` | 6229 | `DATA rtpi/1.77245385090552D0/` |
| `gratio` | 6230 | `DATA third/.333333333333333D0/` |
| `gratio` | 6231 | `DATA d0(1)/.833333333333333D-01/,d0(2)/-.148148148148148D-01/,` |
| `gratio` | 6232 | `+     d0(3)/.115740740740741D-02/,d0(4)/.352733686067019D-03/,` |
| `gratio` | 6233 | `+     d0(5)/-.178755144032922D-03/,d0(6)/.391926317852244D-04/,` |
| `gratio` | 6234 | `+     d0(7)/-.218544851067999D-05/,d0(8)/-.185406221071516D-05/,` |
| `gratio` | 6235 | `+     d0(9)/.829671134095309D-06/,d0(10)/-.176659527368261D-06/,` |
| `gratio` | 6236 | `+     d0(11)/.670785354340150D-08/,d0(12)/.102618097842403D-07/,` |
| `gratio` | 6237 | `+     d0(13)/-.438203601845335D-08/` |
| `gratio` | 6238 | `DATA d10/-.185185185185185D-02/,d1(1)/-.347222222222222D-02/,` |
| `gratio` | 6239 | `+     d1(2)/.264550264550265D-02/,d1(3)/-.990226337448560D-03/,` |
| `gratio` | 6240 | `+     d1(4)/.205761316872428D-03/,d1(5)/-.401877572016461D-06/,` |
| `gratio` | 6241 | `+     d1(6)/-.180985503344900D-04/,d1(7)/.764916091608111D-05/,` |
| `gratio` | 6242 | `+     d1(8)/-.161209008945634D-05/,d1(9)/.464712780280743D-08/,` |
| `gratio` | 6243 | `+     d1(10)/.137863344691572D-06/,d1(11)/-.575254560351770D-07/,` |
| `gratio` | 6244 | `+     d1(12)/.119516285997781D-07/` |
| `gratio` | 6245 | `DATA d20/.413359788359788D-02/,d2(1)/-.268132716049383D-02/,` |
| `gratio` | 6246 | `+     d2(2)/.771604938271605D-03/,d2(3)/.200938786008230D-05/,` |
| `gratio` | 6247 | `+     d2(4)/-.107366532263652D-03/,d2(5)/.529234488291201D-04/,` |
| `gratio` | 6248 | `+     d2(6)/-.127606351886187D-04/,d2(7)/.342357873409614D-07/,` |
| `gratio` | 6249 | `+     d2(8)/.137219573090629D-05/,d2(9)/-.629899213838006D-06/,` |
| `gratio` | 6250 | `+     d2(10)/.142806142060642D-06/` |
| `gratio` | 6251 | `DATA d30/.649434156378601D-03/,d3(1)/.229472093621399D-03/,` |
| `gratio` | 6252 | `+     d3(2)/-.469189494395256D-03/,d3(3)/.267720632062839D-03/,` |
| `gratio` | 6253 | `+     d3(4)/-.756180167188398D-04/,d3(5)/-.239650511386730D-06/,` |
| `gratio` | 6254 | `+     d3(6)/.110826541153473D-04/,d3(7)/-.567495282699160D-05/,` |
| `gratio` | 6255 | `+     d3(8)/.142309007324359D-05/` |
| `gratio` | 6256 | `DATA d40/-.861888290916712D-03/,d4(1)/.784039221720067D-03/,` |
| `gratio` | 6257 | `+     d4(2)/-.299072480303190D-03/,d4(3)/-.146384525788434D-05/,` |
| `gratio` | 6258 | `+     d4(4)/.664149821546512D-04/,d4(5)/-.396836504717943D-04/,` |
| `gratio` | 6259 | `+     d4(6)/.113757269706784D-04/` |
| `gratio` | 6260 | `DATA d50/-.336798553366358D-03/,d5(1)/-.697281375836586D-04/,` |
| `gratio` | 6261 | `+     d5(2)/.277275324495939D-03/,d5(3)/-.199325705161888D-03/,` |
| `gratio` | 6262 | `+     d5(4)/.679778047793721D-04/` |
| `gratio` | 6263 | `DATA d60/.531307936463992D-03/,d6(1)/-.592166437353694D-03/,` |
| `gratio` | 6264 | `+     d6(2)/.270878209671804D-03/` |
| `gratio` | 6265 | `DATA d70/.344367606892378D-03/` |
| `gratio` | 6275 | `IF (a.LT.0.0D0 .OR. x.LT.0.0D0) GO TO 430` |
| `gratio` | 6276 | `IF (a.EQ.0.0D0 .AND. x.EQ.0.0D0) GO TO 430` |
| `gratio` | 6277 | `IF (a*x.EQ.0.0D0) GO TO 420` |
| `gratio` | 6287 | `IF (a.GE.1.0D0) GO TO 10` |
| `gratio` | 6288 | `IF (a.EQ.0.5D0) GO TO 390` |
| `gratio` | 6289 | `IF (x.LT.1.1D0) GO TO 160` |
| `gratio` | 6292 | `IF (u.EQ.0.0D0) GO TO 380` |
| `gratio` | 6293 | `r = u* (1.0D0+gam1(a))` |
| `gratio` | 6300 | `IF (twoa.NE.dble(m)) GO TO 20` |
| `gratio` | 6302 | `IF (a.EQ.dble(i)) GO TO 210` |
| `gratio` | 6310 | `IF (l.EQ.0.0D0) GO TO 370` |
| `gratio` | 6311 | `s = 0.5D0 + (0.5D0-l)` |
| `gratio` | 6313 | `IF (z.GE.700.0D0/a) GO TO 410` |
| `gratio` | 6317 | `IF (abs(s).LE.0.4D0) GO TO 270` |
| `gratio` | 6319 | `t = (1.0D0/a)**2` |
| `gratio` | 6320 | `t1 = (((0.75D0*t-1.0D0)*t+3.5D0)*t-105.0D0)/ (a*1260.0D0)` |
| `gratio` | 6324 | `40 IF (r.EQ.0.0D0) GO TO 420` |
| `gratio` | 6331 | `50 apn = a + 1.0D0` |
| `gratio` | 6335 | `apn = apn + 1.0D0` |
| `gratio` | 6337 | `IF (t.LE.1.D-3) GO TO 70` |
| `gratio` | 6343 | `tol = 0.5D0*acc` |
| `gratio` | 6344 | `80 apn = apn + 1.0D0` |
| `gratio` | 6354 | `ans = (r/a)* (1.0D0+sum)` |
| `gratio` | 6355 | `qans = 0.5D0 + (0.5D0-ans)` |
| `gratio` | 6360 | `100 amn = a - 1.0D0` |
| `gratio` | 6364 | `amn = amn - 1.0D0` |
| `gratio` | 6366 | `IF (abs(t).LE.1.D-3) GO TO 120` |
| `gratio` | 6373 | `amn = amn - 1.0D0` |
| `gratio` | 6383 | `qans = (r/x)* (1.0D0+sum)` |
| `gratio` | 6384 | `ans = 0.5D0 + (0.5D0-qans)` |
| `gratio` | 6389 | `160 an = 3.0D0` |
| `gratio` | 6391 | `sum = x/ (a+3.0D0)` |
| `gratio` | 6392 | `tol = 3.0D0*acc/ (a+1.0D0)` |
| `gratio` | 6393 | `170 an = an + 1.0D0` |
| `gratio` | 6398 | `j = a*x* ((sum/6.0D0-0.5D0/ (a+2.0D0))*x+1.0D0/ (a+1.0D0))` |
| `gratio` | 6402 | `g = 1.0D0 + h` |
| `gratio` | 6403 | `IF (x.LT.0.25D0) GO TO 180` |
| `gratio` | 6404 | `IF (a.LT.x/2.59D0) GO TO 200` |
| `gratio` | 6407 | `180 IF (z.GT.-.13394D0) GO TO 200` |
| `gratio` | 6410 | `ans = w*g* (0.5D0+ (0.5D0-j))` |
| `gratio` | 6411 | `qans = 0.5D0 + (0.5D0-ans)` |
| `gratio` | 6415 | `w = 0.5D0 + (0.5D0+l)` |
| `gratio` | 6417 | `IF (qans.LT.0.0D0) GO TO 380` |
| `gratio` | 6418 | `ans = 0.5D0 + (0.5D0-qans)` |
| `gratio` | 6427 | `c = 0.0D0` |
| `gratio` | 6434 | `c = -0.5D0` |
| `gratio` | 6438 | `c = c + 1.0D0` |
| `gratio` | 6444 | `ans = 0.5D0 + (0.5D0-qans)` |
| `gratio` | 6449 | `250 tol = dmax1(5.0D0*e,acc)` |
| `gratio` | 6450 | `a2nm1 = 1.0D0` |
| `gratio` | 6451 | `a2n = 1.0D0` |
| `gratio` | 6453 | `b2n = x + (1.0D0-a)` |
| `gratio` | 6454 | `c = 1.0D0` |
| `gratio` | 6458 | `c = c + 1.0D0` |
| `gratio` | 6466 | `ans = 0.5D0 + (0.5D0-qans)` |
| `gratio` | 6471 | `270 IF (abs(s).LE.2.0D0*e .AND. a*e*e.GT.3.28D-3) GO TO 430` |
| `gratio` | 6473 | `w = 0.5D0*erfc1(1,sqrt(y))` |
| `gratio` | 6474 | `u = 1.0D0/a` |
| `gratio` | 6476 | `IF (l.LT.1.0D0) z = -z` |
| `gratio` | 6479 | `280 IF (abs(s).LE.1.D-3) GO TO 340` |
| `gratio` | 6506 | `310 IF (l.LT.1.0D0) GO TO 320` |
| `gratio` | 6508 | `ans = 0.5D0 + (0.5D0-qans)` |
| `gratio` | 6512 | `qans = 0.5D0 + (0.5D0-ans)` |
| `gratio` | 6517 | `330 IF (a*e*e.GT.3.28D-3) GO TO 430` |
| `gratio` | 6518 | `c = 0.5D0 + (0.5D0-y)` |
| `gratio` | 6519 | `w = (0.5D0-sqrt(y)* (0.5D0+ (0.5D0-y/3.0D0))/rtpi)/c` |
| `gratio` | 6520 | `u = 1.0D0/a` |
| `gratio` | 6522 | `IF (l.LT.1.0D0) z = -z` |
| `gratio` | 6547 | `370 ans = 0.0D0` |
| `gratio` | 6548 | `qans = 1.0D0` |
| `gratio` | 6551 | `380 ans = 1.0D0` |
| `gratio` | 6552 | `qans = 0.0D0` |
| `gratio` | 6555 | `390 IF (x.GE.0.25D0) GO TO 400` |
| `gratio` | 6557 | `qans = 0.5D0 + (0.5D0-ans)` |
| `gratio` | 6561 | `ans = 0.5D0 + (0.5D0-qans)` |
| `gratio` | 6564 | `410 IF (abs(s).LE.2.0D0*e) GO TO 430` |
| `gratio` | 6570 | `430 ans = 2.0D0` |
| `rexp` | 7005 | `DOUBLE PRECISION FUNCTION rexp(x)` |
| `rexp` | 7010 | `DOUBLE PRECISION x` |
| `rexp` | 7013 | `DOUBLE PRECISION p1,p2,q1,q2,q3,q4,w` |
| `rexp` | 7019 | `DATA p1/.914041914819518D-09/,p2/.238082361044469D-01/,` |
| `rexp` | 7020 | `+     q1/-.499999999085958D+00/,q2/.107141568980644D+00/,` |
| `rexp` | 7021 | `+     q3/-.119041179760821D-01/,q4/.595130811860248D-03/` |
| `rexp` | 7025 | `IF (abs(x).GT.0.15D0) GO TO 10` |
| `rexp` | 7026 | `rexp = x* (((p2*x+p1)*x+1.0D0)/ ((((q4*x+q3)*x+q2)*x+q1)*x+1.0D0))` |
| `rexp` | 7030 | `IF (x.GT.0.0D0) GO TO 20` |
| `rexp` | 7031 | `rexp = (w-0.5D0) - 0.5D0` |
| `rexp` | 7034 | `20 rexp = w* (0.5D0+ (0.5D0-1.0D0/w))` |
| `rlog` | 7039 | `DOUBLE PRECISION FUNCTION rlog(x)` |
| `rlog` | 7044 | `DOUBLE PRECISION x` |
| `rlog` | 7047 | `DOUBLE PRECISION a,b,p0,p1,p2,q1,q2,r,t,u,w,w1` |
| `rlog` | 7054 | `DATA a/.566749439387324D-01/` |
| `rlog` | 7055 | `DATA b/.456512608815524D-01/` |
| `rlog` | 7056 | `DATA p0/.333333333333333D+00/,p1/-.224696413112536D+00/,` |
| `rlog` | 7057 | `+     p2/.620886815375787D-02/` |
| `rlog` | 7058 | `DATA q1/-.127408923933623D+01/,q2/.354508718369557D+00/` |
| `rlog` | 7062 | `IF (x.LT.0.61D0 .OR. x.GT.1.57D0) GO TO 40` |
| `rlog` | 7063 | `IF (x.LT.0.82D0) GO TO 10` |
| `rlog` | 7064 | `IF (x.GT.1.18D0) GO TO 20` |
| `rlog` | 7068 | `u = (x-0.5D0) - 0.5D0` |
| `rlog` | 7069 | `w1 = 0.0D0` |
| `rlog` | 7072 | `10 u = dble(x) - 0.7D0` |
| `rlog` | 7073 | `u = u/0.7D0` |
| `rlog` | 7074 | `w1 = a - u*0.3D0` |
| `rlog` | 7077 | `20 u = 0.75D0*dble(x) - 1.D0` |
| `rlog` | 7078 | `w1 = b + u/3.0D0` |
| `rlog` | 7082 | `30 r = u/ (u+2.0D0)` |
| `rlog` | 7084 | `w = ((p2*t+p1)*t+p0)/ ((q2*t+q1)*t+1.0D0)` |
| `rlog` | 7085 | `rlog = 2.0D0*t* (1.0D0/ (1.0D0-r)-r*w) + w1` |
| `rlog` | 7089 | `40 r = (x-0.5D0) - 0.5D0` |
| `spmpar` | 7095 | `DOUBLE PRECISION FUNCTION spmpar(i)` |
| `spmpar` | 7125 | `DOUBLE PRECISION b,binv,bm1,one,w,z` |
| `spmpar` | 7146 | `one = dble(1)` |
| `spmpar` | 7158 | `one = dble(1)` |

## Include-file precision declarations (live includes)

| File | Line | Source |
|---|---|---|
| `crandom3.inc` | 15 | `double precision g_dsum(nrparm,12)` |
| `crandom3.inc` | 16 | `double precision g_ssum(nrparm,12)` |
