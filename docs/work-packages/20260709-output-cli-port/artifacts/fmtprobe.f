      program fmtprobe
      integer ib, ir
      real v, vn
      equivalence (v, ib)
      integer los(3), his(3), sts(3)
      data los /897581056, 939524096, 1092616192/
      data his /939524096, 1092616192, 1157234688/
      data sts /251, 61, 127/
      open(20,file='fmt_pairs.txt',status='unknown')
      do 30 ir = 1, 3
        ib = los(ir)
 10     continue
          write(20,100) ib, v, v, v, v, v, v, v, v, v
          vn = -v
          write(20,101) ib, vn, vn, vn, vn, vn, vn, vn, vn, vn
          ib = ib + sts(ir)
        if (ib .lt. his(ir)) goto 10
 30   continue
      v = 0.0
      write(20,100) ib, v, v, v, v, v, v, v, v, v
      vn = -v
      write(20,101) ib, vn, vn, vn, vn, vn, vn, vn, vn, vn
 100  format(z8.8,'|',f4.0,'|',f4.1,'|',f4.2,'|',f5.1,'|',f5.2,'|',
     1       f6.2,'|',f7.5,'|',f8.5,'|',f9.2,'|')
 101  format('-',z8.8,'|',f4.0,'|',f4.1,'|',f4.2,'|',f5.1,'|',f5.2,'|',
     1       f6.2,'|',f7.5,'|',f8.5,'|',f9.2,'|')
      stop
      end
