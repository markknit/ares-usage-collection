# Replacing an incomplete installation package

The checksum-bypass recovery installer has been removed from the simplified
v1.13 source. Historical test records describe the earlier implementation.

Use the normal command: `sudo bash install_offline.sh ARES-S00XX`.

The package check runs automatically. If it reports an incomplete or changed
package, copy the complete ZIP again and extract it into a new folder. Do not
edit checksum files or switch to an unverified installation mode.

For another installation failure, send the displayed installation log to ARES
support. Support may restore a disposable server from its base image when
appropriate. A fresh server image does not repair an incomplete package.
