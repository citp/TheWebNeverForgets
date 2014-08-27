data.3p <- read.csv('/home/steven/Downloads/with_cookies.csv')
sub <- seq(1, dim(data.3p)[1], 10)
line.width <- 1.5
plot(x=1:dim(data.3p)[1], y=data.3p[,1], lwd=line.width, 
     xlab="Rank of domain (decreasing order)", 
     ylab="Proportion of history known",
     xlim=c(0,dim(data.3p)[1]),
     ylim=c(0,.8), type='l', cex.axis=.8, cex.lab=.8)
points(x=seq(1, dim(data.3p)[1], 10), y=data.3p[,1][sub], lwd=line.width, col='black')
lines(x=1:dim(data.3p)[1], y=data.3p[,2], lwd=line.width, col='firebrick2', pch=1)
points(x=seq(1, dim(data.3p)[1], 10), y=data.3p[,2][sub], lwd=line.width, col='firebrick2', pch=2)
lines(x=1:dim(data.3p)[1], y=data.3p[,3], lwd=line.width, col='steelblue')
points(x=seq(1, dim(data.3p)[1], 10), y=data.3p[,3][sub], lwd=line.width, col='steelblue', pch=3)
legend("topright",c("No Merge","One Hop        ","Two Hops"), col=c("black","firebrick2","steelblue"), 
       lty=c(1,1), lwd=line.width, cex=0.6, pch=c(1,2,3))

data.1p <- read.csv('/home/steven/Downloads/cookies_blocked.csv')
sub <- seq(1, dim(data.1p)[1], 6)
line.width <- 1.5
plot(x=1:dim(data.1p)[1], y=data.1p[,1], lwd=line.width, 
     xlab="Rank of domain (decreasing order)", 
     ylab="Proportion of history known",
     xlim=c(0,dim(data.3p)[1]),
     ylim=c(0,.8), type='l')
#lines(x=1:dim(data.1p)[1], y=data.1p[,1], lwd=line.width, col='black', pch=1)
points(x=sub, y=data.1p[,1][sub], lwd=line.width, col='black')
lines(x=1:dim(data.1p)[1], y=data.1p[,2], lwd=line.width, col='firebrick2', pch=1)
points(x=sub, y=data.1p[,2][sub], lwd=line.width, col='firebrick2', pch=2)
lines(x=1:dim(data.1p)[1], y=data.1p[,3], lwd=line.width, col='steelblue')
points(x=sub, y=data.1p[,3][sub], lwd=line.width, col='steelblue', pch=3)
legend("topright",c("No Merge","One Hop        ","Two Hops"), col=c("black","firebrick2","steelblue"), 
       lty=c(1,1), lwd=line.width, cex=0.6, pch=c(1,2,3))