      program tieprobe
      real v(12)
      integer i
      data v /0.25, 0.75, 1.25, 1.75, 2.5, 3.5, 0.125, 0.375,
     1        0.0625, 12.5, 0.005859375, 62.5/
      do 10 i = 1, 12
        write(*,100) v(i), v(i), v(i), v(i)
 10   continue
 100  format(f4.0,'|',f4.1,'|',f5.2,'|',f7.3,'|')
      end
