#Attempt to use neopo as python module to configure and build project
import neopo
neopo.create("testpy", "argon", "2.0.0-rc.3")
neopo.build("testpy")
