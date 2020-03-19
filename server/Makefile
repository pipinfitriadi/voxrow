# Copyright 2020 Pipin Fitriadi <pipinfitriadi@gmail.com>

# Licensed under the Microsoft Reference Source License (MS-RSL)

# This license governs use of the accompanying software. If you use the
# software, you accept this license. If you do not accept the license, do not
# use the software.

# 1. Definitions

# The terms "reproduce," "reproduction" and "distribution" have the same
# meaning here as under U.S. copyright law.

# "You" means the licensee of the software.

# "Your company" means the company you worked for when you downloaded the
# software.

# "Reference use" means use of the software within your company as a reference,
# in read only form, for the sole purposes of debugging your products,
# maintaining your products, or enhancing the interoperability of your
# products with the software, and specifically excludes the right to
# distribute the software outside of your company.

# "Licensed patents" means any Licensor patent claims which read directly on
# the software as distributed by the Licensor under this license.

# 2. Grant of Rights

# (A) Copyright Grant- Subject to the terms of this license, the Licensor
# grants you a non-transferable, non-exclusive, worldwide, royalty-free
# copyright license to reproduce the software for reference use.

# (B) Patent Grant- Subject to the terms of this license, the Licensor grants
# you a non-transferable, non-exclusive, worldwide, royalty-free patent
# license under licensed patents for reference use.

# 3. Limitations

# (A) No Trademark License- This license does not grant you any rights to use
# the Licensor's name, logo, or trademarks.

# (B) If you begin patent litigation against the Licensor over patents that
# you think may apply to the software (including a cross-claim or counterclaim
# in a lawsuit), your license to the software ends automatically.

# (C) The software is licensed "as-is." You bear the risk of using it. The
# Licensor gives no express warranties, guarantees or conditions. You may have
# additional consumer rights under your local laws which this license cannot
# change. To the extent permitted under your local laws, the Licensor excludes
# the implied warranties of merchantability, fitness for a particular purpose
# and non-infringement.

# Makefile Tutorial
# https://makefiletutorial.com/
# Passing additional variables from command line to make
# https://stackoverflow.com/questions/2826029/passing-additional-variables-from-command-line-to-mak

# Referensi:
# How to Harden your Ubuntu 18.04 Server
# https://hostadvice.com/how-to/how-to-harden-your-ubuntu-18-04-server/
# How to Harden Ubuntu Server 18.04 in 5 Easy Steps
# https://www.lifewire.com/harden-ubuntu-server-security-4178243
# How to Secure and Harden Cloud/VPS VM (Ubuntu/CentOS)?
# https://geekflare.com/cloud-vm-security-guide/#3-Disable-Password-based-Authentication
# How to harden Ubuntu Server 16.04 security in five steps
# https://www.techrepublic.com/article/how-to-harden-ubuntu-server-16-04-security-in-five-steps/

# Define your own function in a Makefile
# https://coderwall.com/p/cezf6g/define-your-own-function-in-a-makefile
define install_program
	@if [ $1 ]\
		&& ! [ -x "$(command -v $1)" ]; then\
			if [ $2 ]; then\
				sudo apt-get install $2 -y;\
			else\
				sudo apt-get install $1 -y;\
			fi;\
		fi
endef

# Buat SSH Key Pair di komputer lokal dan salin SSH Public Key ke server.
# https://www.digitalocean.com/community/tutorials/how-to-set-up-ssh-keys-on-ubuntu-1804
initial_setup_server: update_server\
	gitflow\
	create_user\
	firewall\
	secure_sharedmemory\
	timezone_ntp\
	harden_network\
	ddos_protection\
	deactivate_root\
	fail2ban_setup
	@echo "Initial setup server is finished!"
	@sudo reboot

# Authenticate to Ubuntu Server Using SSH Keys.
# https://www.digitalocean.com/community/tutorials/how-to-set-up-ssh-keys-on-ubuntu-1804
# WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED
# https://www.digitalocean.com/community/questions/warning-remote-host-identification-has-changed
local_ssh_key_to_server:
	@echo "Authenticate to Ubuntu Server Using SSH Keys."
	@read -p "Remote host: " remote_host;\
		read -p "Username: " username;\
		if [ $${remote_host} ] && [ $${username} ]; then\
			ssh-keygen -R $${remote_host};\
			cat ~/.ssh/id_rsa.pub\
			| ssh $${username}@$${remote_host}\
			"mkdir -p ~/.ssh\
				&& touch ~/.ssh/authorized_keys\
				&& chmod -R go= ~/.ssh\
				&& cat >> ~/.ssh/authorized_keys";\
		fi

update_server:
	@echo "Update Server."
	@sudo apt-get update

gitflow:
	@echo "Install Git-Flow"
	$(call install_program, git-flow)

# Enabling External Access for Your Regular User
# https://www.digitalocean.com/community/tutorials/initial-server-setup-with-ubuntu-18-04
create_user:
	@echo "Membuat akun reguler server dan pilihan untuk memberikan hak akses superuser ke akun tersebut."
	@read -p "Username: " username;\
		read -p "Is superuser? [y/n] " is_superuser;\
		is_superuser=$${is_superuser:-n};\
		if [ $${username} ]; then\
			sudo adduser $${username};\
		fi;\
		if [ $${is_superuser} = y ]; then\
			sudo usermod -aG sudo $${username};\
			rsync --archive --chown=$${username}:$${username} ~/.ssh /home/$${username};\
		fi

firewall:
	@echo "Memasangkan firewall sederhana."
	@sudo ufw app list
	@sudo ufw allow OpenSSH
	@sudo ufw allow http
	@sudo ufw allow https
	@sudo ufw enable
	@sudo ufw status verbose

secure_sharedmemory:
	@echo "Mengamankan Shared Memory."
	@sudo cp -f fstab /etc/fstab

# Pasang zona waktu & NTP.
# https://medium.com/@AKcryptoGUY/how-to-secure-vps-hyper-v-9ceee0d1c2a9
timezone_ntp:
	@echo "Pasang zona waktu & NTP."
	$(call install_program, dbus)
	@read -p "Server's timezone? [Asia/Jakarta] " timezone;\
		timezone=$${timezone:-"Asia/Jakarta"};\
		sudo timedatectl set-timezone $${timezone}
	$(call install_program, ntp)
	@echo Timezone: $$(cat /etc/timezone)

# Harden the networking layer.
# https://medium.com/@AKcryptoGUY/how-to-secure-vps-hyper-v-9ceee0d1c2a9
harden_network:
	@echo "Harden the networking layer."
	@sudo cp -f sysctl.conf /etc/sysctl.conf

# DDos Protection.
# https://medium.com/@AKcryptoGUY/how-to-secure-vps-hyper-v-9ceee0d1c2a9
ddos_protection:
	@echo "DDos Protection."
	@sudo cp -f before.rules /etc/ufw/before.rules

deactivate_root:
	@echo "Non-aktifkan login SSH user root dan autentikasi password SSH."
	@sudo cp -f sshd_config /etc/ssh/sshd_config
	@sudo systemctl restart sshd

fail2ban_setup:
	@echo "Pasang Fail2ban."
	$(call install_program, fail2ban)
	@sudo cp -f jail.local /etc/fail2ban/jail.local
	@sudo systemctl restart fail2ban
