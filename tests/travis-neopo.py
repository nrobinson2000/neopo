#Attempt to use neopo as python module to configure and build project
import neopo
neopo.configure("argon", "2.0.0-rc.3", "test")
neopo.build("test", "-v")