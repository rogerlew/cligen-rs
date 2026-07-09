c Stage C direct-vector driver.  Linked only into the copied tap build.
c Every floating result is emitted as its IEEE bit pattern.
      subroutine stagec_vectors
      integer nc(13),i,j,m,nt,ntd,jday,mo,nday,status,which,ind
      integer jdt,ipmpar
      integer ib1,ib2,ib3
      integer*8 db(8)
      real rv(3)
      double precision dv(8),p,q,x,df,bound,cum,ccum,fx,xlo,xhi
      double precision erf,erfc1,exparg,gam1,gamma,rexp,rlog,spmpar
      logical qleft,qhi
      external erf,erfc1,exparg,gam1,gamma,rexp,rlog,spmpar
      equivalence (rv(1),ib1),(rv(2),ib2),(rv(3),ib3)
      equivalence (dv,db)
      data nc/0,31,59,90,120,151,181,212,243,273,304,334,365/

c Calendar: boundary, leap, and ordinary dates.
      do 10 nt=0,1
        do 20 m=1,12
          i=1
          write(95,9501) 'JDT',nt,m,i,jdt(nc,i,m,nt)
          i=15
          write(95,9501) 'JDT',nt,m,i,jdt(nc,i,m,nt)
          i=nc(m+1)-nc(m)
          if(m.eq.2) i=i+nt
          write(95,9501) 'JDT',nt,m,i,jdt(nc,i,m,nt)
 20     continue
 10   continue
      do 30 ntd=365,366
        do 40 jday=1,ntd
          i=jday
          call jlt(ntd,i,mo,nday)
          write(95,9501) 'JLT',ntd,jday,mo,nday
 40     continue
 30   continue
      ntd=166
      jday=166
      i=jday
      call jlt(ntd,i,mo,nday)
      write(95,9501) 'JLT',ntd,jday,mo,nday

c QC confidence routines.
      rv(1)=0.0
      call conflm(rv(1),100,0.0,1.0,rv(2))
      write(95,9502) 'CONFLM',100,ib1,ib2
      rv(1)=0.2
      call conflm(rv(1),100,0.0,1.0,rv(2))
      write(95,9502) 'CONFLM',100,ib1,ib2
      rv(1)=1.0
      call conflm(rv(1),0,0.0,1.0,rv(2))
      write(95,9502) 'CONFLM',0,ib1,ib2
      rv(1)=100.0
      call confls(rv(1),100,rv(2))
      write(95,9502) 'CONFLS',100,ib1,ib2
      rv(1)=120.0
      call confls(rv(1),100,rv(2))
      write(95,9502) 'CONFLS',100,ib1,ib2
      rv(1)=0.0
      call confls(rv(1),0,rv(2))
      write(95,9502) 'CONFLS',0,ib1,ib2

c CDF/CUM entry points.  WHICH=2/3 exercise both reverse-communication
c state machines through CDFCHI.
      which=1
      x=10.0d0
      df=8.0d0
      p=0.0d0
      q=0.0d0
      bound=0.0d0
      call cdfchi(which,p,q,x,df,status,bound)
      call tapcdf(which,status,p,q,x,df,bound)
      which=2
      p=0.75d0
      q=0.25d0
      x=0.0d0
      df=8.0d0
      bound=0.0d0
      call cdfchi(which,p,q,x,df,status,bound)
      call tapcdf(which,status,p,q,x,df,bound)
      which=3
      p=0.75d0
      q=0.25d0
      x=10.0d0
      df=0.0d0
      bound=0.0d0
      call cdfchi(which,p,q,x,df,status,bound)
      call tapcdf(which,status,p,q,x,df,bound)
      x=10.0d0
      df=8.0d0
      call cumchi(x,df,cum,ccum)
      dv(1)=x
      dv(2)=df
      dv(3)=cum
      dv(4)=ccum
      write(95,9503) 'CUMCHI',0,(db(i),i=1,4)
      x=5.0d0
      df=4.0d0
      call cumgam(x,df,cum,ccum)
      dv(1)=x
      dv(2)=df
      dv(3)=cum
      dv(4)=ccum
      write(95,9503) 'CUMGAM',0,(db(i),i=1,4)

c Direct DINVR sequence for f(x)=x*x-2 on [0,10].
      call dstinv(0.0d0,10.0d0,0.5d0,0.5d0,5.0d0,1.0d-50,1.0d-8)
      status=0
      x=1.0d0
      fx=0.0d0
      qleft=.false.
      qhi=.false.
 50   call dinvr(status,x,fx,qleft,qhi)
      dv(1)=x
      dv(2)=fx
      write(95,9504) 'DINVR',status,qleft,qhi,db(1),db(2)
      if(status.eq.1) then
        fx=x*x-2.0d0
        goto 50
      endif

c Direct DINVR sequence that takes the lower-stepping path first.
      call dstinv(0.0d0,10.0d0,0.5d0,0.5d0,5.0d0,1.0d-50,1.0d-8)
      status=0
      x=9.0d0
      fx=0.0d0
      qleft=.false.
      qhi=.false.
 55   call dinvr(status,x,fx,qleft,qhi)
      dv(1)=x
      dv(2)=fx
      write(95,9504) 'DINVRL',status,qleft,qhi,db(1),db(2)
      if(status.eq.1) then
        fx=x*x-2.0d0
        goto 55
      endif

c Direct DZROR sequence for the same root.
      call dstzr(0.0d0,10.0d0,1.0d-50,1.0d-8)
      status=0
      x=0.0d0
      fx=0.0d0
      xlo=0.0d0
      xhi=0.0d0
      qleft=.false.
      qhi=.false.
 60   call dzror(status,x,fx,xlo,xhi,qleft,qhi)
      dv(1)=x
      dv(2)=fx
      dv(3)=xlo
      dv(4)=xhi
      write(95,9505) 'DZROR',status,qleft,qhi,(db(i),i=1,4)
      if(status.eq.1) then
        fx=x*x-2.0d0
        goto 60
      endif

c Scalar ACM functions, covering every source branch that is reachable
c from CDFCHI plus the log/sine paths requiring transcendental adjudication.
      do 70 i=1,7
        if(i.eq.1) x=-5.9d0
        if(i.eq.2) x=-2.0d0
        if(i.eq.3) x=-0.5d0
        if(i.eq.4) x=0.0d0
        if(i.eq.5) x=0.5d0
        if(i.eq.6) x=2.0d0
        if(i.eq.7) x=5.9d0
        dv(1)=x
        dv(2)=erf(x)
        write(95,9503) 'ERF',0,db(1),db(2)
 70   continue
      do 80 ind=0,1
        do 90 i=1,5
          if(i.eq.1) x=-6.0d0
          if(i.eq.2) x=-0.5d0
          if(i.eq.3) x=0.0d0
          if(i.eq.4) x=2.0d0
          if(i.eq.5) x=101.0d0
          dv(1)=x
          dv(2)=erfc1(ind,x)
          write(95,9503) 'ERFC1',ind,db(1),db(2)
 90     continue
 80   continue
      do 100 i=0,1
        dv(1)=exparg(i)
        write(95,9503) 'EXPARG',i,db(1)
 100  continue
      do 110 i=1,5
        x=-1.0d0+0.5d0*i
        dv(1)=x
        dv(2)=gam1(x)
        write(95,9503) 'GAM1',0,db(1),db(2)
 110  continue
      do 120 i=1,7
        if(i.eq.1) x=-16.2d0
        if(i.eq.2) x=-2.5d0
        if(i.eq.3) x=0.5d0
        if(i.eq.4) x=1.0d0
        if(i.eq.5) x=5.0d0
        if(i.eq.6) x=16.2d0
        if(i.eq.7) x=1001.0d0
        dv(1)=x
        dv(2)=gamma(x)
        write(95,9503) 'GAMMA',0,db(1),db(2)
 120  continue
      call tapgratio(0.5d0,0.1d0,0)
      call tapgratio(0.2d0,0.1d0,0)
      call tapgratio(0.5d0,2.0d0,0)
      call tapgratio(2.0d0,1.0d0,0)
      call tapgratio(8.0d0,10.0d0,0)
      call tapgratio(30.0d0,29.0d0,0)
      call tapgratio(30.0d0,50.0d0,0)
      call tapgratio(30.0d0,29.0d0,1)
      call tapgratio(30.0d0,29.0d0,2)
      do 130 i=1,10
        write(95,9501) 'IPMPAR',i,ipmpar(i),0,0
 130  continue
      do 140 i=1,5
        if(i.eq.1) x=-1.0d0
        if(i.eq.2) x=-0.15d0
        if(i.eq.3) x=0.0d0
        if(i.eq.4) x=0.15d0
        if(i.eq.5) x=1.0d0
        dv(1)=x
        dv(2)=rexp(x)
        write(95,9503) 'REXP',0,db(1),db(2)
 140  continue
      do 150 i=1,8
        if(i.eq.1) x=0.5d0
        if(i.eq.2) x=0.61d0
        if(i.eq.3) x=0.7d0
        if(i.eq.4) x=0.82d0
        if(i.eq.5) x=1.0d0
        if(i.eq.6) x=1.18d0
        if(i.eq.7) x=1.57d0
        if(i.eq.8) x=2.0d0
        dv(1)=x
        dv(2)=rlog(x)
        write(95,9503) 'RLOG',0,db(1),db(2)
 150  continue
      do 160 i=1,3
        dv(1)=spmpar(i)
        write(95,9503) 'SPMPAR',i,db(1)
 160  continue

 9501 format(a8,1x,4(i12,1x))
 9502 format(a8,1x,i12,1x,2(z8.8,1x))
 9503 format(a8,1x,i12,1x,8(z16.16,1x))
 9504 format(a8,1x,i12,1x,2(l1,1x),2(z16.16,1x))
 9505 format(a8,1x,i12,1x,2(l1,1x),4(z16.16,1x))
      return
      end

      subroutine tapcdf(which,status,p,q,x,df,bound)
      integer which,status,i
      integer*8 db(5)
      double precision p,q,x,df,bound,dv(5)
      equivalence (dv,db)
      dv(1)=p
      dv(2)=q
      dv(3)=x
      dv(4)=df
      dv(5)=bound
      write(95,9510) 'CDFCHI',which,status,(db(i),i=1,5)
 9510 format(a8,1x,2(i12,1x),5(z16.16,1x))
      return
      end

      subroutine tapgratio(a,x,ind)
      integer ind,i
      integer*8 db(4)
      double precision a,x,ans,qans,dv(4)
      equivalence (dv,db)
      call gratio(a,x,ans,qans,ind)
      dv(1)=a
      dv(2)=x
      dv(3)=ans
      dv(4)=qans
      write(95,9520) 'GRATIO',ind,(db(i),i=1,4)
 9520 format(a8,1x,i12,1x,4(z16.16,1x))
      return
      end
