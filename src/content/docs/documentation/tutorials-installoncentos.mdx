---
title: "Installing OpenSIPS 1.6.3 on CentOS 5.5 with mi-xmlrpc"
description: "Recently, I heard from some people that is difficult to install OpenSIPS on CentOS, mainly the mi_xmlrpc module. Some servers do not support Debian or Ubuntu..."
---

Recently, I heard from some people that is difficult to install OpenSIPS on CentOS, mainly the mi_xmlrpc module. Some servers do not support Debian or Ubuntu, where the compilation process is quite simple,  but in most cases they support RedHat and CentOS. The instructions below are valid for both. Using the preinstalled operating system is sometimes valuable because of the tech support and improved drivers. The objective of this tutorial is to show you how to compile successfully OpenSIPS on CentOS. This configuration was tested with CentOS 5.5.

The installation process is described step by step below:

*Step 1*: install the dependencies.

```bash
yum install gcc gcc-c++ bison flex zlib-devel openssl-devel mysql-devel subversion pcre-devel
```

*Step 2*: Download the OpenSIPS source from the svn repository.

```text
cd /usr/src
svn co https://opensips.svn.sourceforge.net/svnroot/opensips/branches/1.6 opensips_1_6
```

*Step 3*: Compile the library xmlrpc-c. If you forget to use --disable-abyss-threads, the system will eventually dump the core because OpenSIPS is multiprocess but not multithreaded.  The newest versions of xmlrpc compile by default with threads enabled. This problem do not occur with Debian or Ubuntu because they use an old version of xml-rpc (0.9.1) that does not support threads. 

```bash
wget http://sourceforge.net/projects/xmlrpc-c/files/Xmlrpc-c%20Super%20Stable/1.06.41/xmlrpc-c-1.06.41.tgz
tar -xzvf xmlrpc-c-1.06.41.tgz
./configure --disable-abyss-threads
make
make install
```

By default xmlrpc is installed at /usr/local/lib. If your system can only find libraries at /usr/lib, please create a symbolic link pointing to the correct library or change the library path. 

*Step 4*: Use your favorite Linux editor to edit the Makefile

Remove from the “Exclude=” (line 52) the modules db_mysql and mi_xmlrpc. This will make the compilation process include the modules db_mysql and mi_xmlrpc.

```text
cd /usr/src/opensips_1_6
vi Makefile
```

*Step 5*: Compile and install the core and modules. 

```bash
cd opensips_1_6
make prefix=/ all
make prefix=/ install
```
