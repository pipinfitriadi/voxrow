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

# Define your own function in a Makefile
# https://coderwall.com/p/cezf6g/define-your-own-function-in-a-makefile
define install_program
	@if [ $1 ]\
	&& ! [ -x "$(command -v $1)" ]; then\
		if [ $2 ]; then\
			sudo apt-get install $2;\
		else\
			sudo apt-get install $1;\
		fi;\
	fi
endef

update_server:
	@sudo apt-get update

gitflow:
	$(call install_program, git-flow)

# Membuat akun reguler server dan pilihan untuk memberikan hak akses superuser ke akun tersebut.
create_user:
	@read -p "Username: " username;\
	read -p "Is superuser? [y/n] " is_superuser;\
	is_superuser=$${is_superuser:-n};\
	if [ $${username} ]; then\
		sudo adduser $${username};\
	fi;\
	if [ $${is_superuser} = y ]; then\
		sudo usermod -aG sudo $${username};\
	fi

# Memasangkan firewall sederhana.
firewall:
	@sudo ufw app list
	@sudo ufw allow http
	@sudo ufw allow https
	@sudo ufw enable
	@sudo ufw status verbose

# Non-aktifkan login SSH user root dan autentikasi password SSH.
deactivate_root:
	@sudo cp -f sshd_config /etc/ssh/sshd_config
	@sudo systemctl restart sshd

secure_sharedmemory:
	@sudo cp -f fstab /etc/fstab

fail2ban_setup:
	$(call install_program, fail2ban)
	@sudo cp -f fail2ban /etc/fail2ban/jail.local
	@sudo systemctl restart fail2ban
