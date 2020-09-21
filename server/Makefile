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
	@if [ $1 ] \
	&& ! [ -x "$(command -v $1)" ]; then \
		if [ $2 ]; then \
			sudo apt-get install -y $2; \
		else\
			sudo apt-get install -y $1; \
		fi; \
	fi
endef

# Buat SSH Key Pair di komputer lokal dan salin SSH Public Key ke server.
# https://www.digitalocean.com/community/tutorials/how-to-set-up-ssh-keys-on-ubuntu-1804
initial_setup_server: update_server \
	gitflow \
	firewall \
	timezone_ntp \
	secure_sharedmemory \
	harden_network \
	ddos_protection \
	fail2ban_setup \
	docker_install \
	dockercompose \
	gitlabrunner \
	create_superuser \
	create_deployer \
	deactivate_root
	@echo "===================== Initial setup server is finished! ====================="
	@sudo reboot

# Authenticate to Ubuntu Server Using SSH Keys.
# https://www.digitalocean.com/community/tutorials/how-to-set-up-ssh-keys-on-ubuntu-1804
# WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED
# https://www.digitalocean.com/community/questions/warning-remote-host-identification-has-changed
local_sshkey_to_server:
	@echo "===================== Authenticate to Ubuntu Server Using SSH Keys ====================="
	@read -p "Remote host: " remote_host; \
		read -p "Username: " username; \
		if [ $$remote_host ] && [ $$username ]; then \
			ssh-keygen -R $$remote_host; \
			cat ~/.ssh/id_rsa.pub \
			| ssh $$username@$$remote_host \
			"mkdir -p ~/.ssh \
			&& touch ~/.ssh/authorized_keys \
			&& chmod -R go= ~/.ssh \
			&& cat >> ~/.ssh/authorized_keys"; \
			echo "Authenticate is done!"; \
		fi

update_server:
	@echo "===================== Update Server ====================="
	@sudo apt-get update

gitflow:
	@echo "Install Git-Flow"
	$(call install_program, git-flow)

firewall:
	@echo "===================== Memasangkan firewall sederhana ====================="
	@sudo ufw app list
	@sudo ufw allow OpenSSH
	@sudo ufw allow http
	@sudo ufw allow https
	@sudo ufw enable
	@sudo ufw status verbose

# Pasang zona waktu & NTP.
# https://medium.com/@AKcryptoGUY/how-to-secure-vps-hyper-v-9ceee0d1c2a9
timezone_ntp:
	@echo "===================== Pasang zona waktu & NTP ====================="
	$(call install_program, dbus)
	@read -p "Server's timezone? [Asia/Jakarta] " timezone; \
		timezone=$${timezone:-"Asia/Jakarta"}; \
		sudo timedatectl set-timezone $$timezone
	$(call install_program, ntp)
	@echo Timezone: $$(cat /etc/timezone)

secure_sharedmemory:
	@echo "===================== Mengamankan Shared Memory ====================="
	@sudo echo 'tmpfs /run/shm tmpfs defaults,noexec,nosuid 0 0' >> /etc/fstab

# Harden the networking layer.
# https://medium.com/@AKcryptoGUY/how-to-secure-vps-hyper-v-9ceee0d1c2a9
harden_network:
	@echo "===================== Harden the networking layer ====================="
	@sudo cp -f install/sysctl.conf /etc/sysctl.conf

# DDos Protection.
# https://medium.com/@AKcryptoGUY/how-to-secure-vps-hyper-v-9ceee0d1c2a9
ddos_protection:
	@echo "===================== DDos Protection ====================="
	@sudo cp -f install/before.rules /etc/ufw/before.rules

fail2ban_setup:
	@echo "===================== Pasang Fail2ban ====================="
	$(call install_program, fail2ban)
	@sudo cp -f install/jail.local /etc/fail2ban/jail.local
	@sudo systemctl restart fail2ban

# Get Docker Engine - Community for Ubuntu
# https://docs.docker.com/install/linux/docker-ce/ubuntu/
docker_install:
	@echo "===================== Pasang Docker ====================="
	@sudo apt-get remove docker docker-engine docker.io containerd runc
	@sudo apt-get install -y apt-transport-https ca-certificates curl gnupg-agent software-properties-common
	@curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
	@sudo apt-key fingerprint 0EBFCD88
	@echo "===================== Verify that you now have the key with the fingerprint ===================== "
	@echo "===================== 9DC8 5822 9FC7 DD38 854A E2D8 8D81 803C 0EBF CD88, ===================== "
	@echo "===================== by searching for the last 8 characters of the fingerprint ===================== "
	@sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $$(lsb_release -cs) stable"
	@sudo apt-get install -y docker-ce docker-ce-cli containerd.io
	@sudo docker run --rm hello-world
	@docker rmi hello-world

# Install Docker Compose
# https://docs.docker.com/compose/install/
dockercompose:
	@echo "===================== Pasang Docker Compose ====================="
	$(call install_program, curl)
	@sudo curl -L "https://github.com/docker/compose/releases/download/1.25.4/docker-compose-$$(uname -s)-$$(uname -m)" -o /usr/local/bin/docker-compose
	@sudo chmod +x /usr/local/bin/docker-compose
	@docker-compose --version

# Install GitLab Runner
# https://docs.gitlab.com/runner/install/linux-repository.html
gitlabrunner:
	@echo "===================== Pasang GitLab Runner ====================="
	$(call install_program, curl)
	@curl -L https://packages.gitlab.com/install/repositories/runner/gitlab-runner/script.deb.sh | sudo bash
	$(call install_program, gitlab-runner)
	@sudo usermod -aG docker gitlab-runner
	@sudo service docker restart

# Enabling External Access for Your Regular User
# https://www.digitalocean.com/community/tutorials/initial-server-setup-with-ubuntu-18-04
# How do I edit /etc/sudoers from a script?
# https://stackoverflow.com/questions/323957/how-do-i-edit-etc-sudoers-from-a-script
# how to pass environment variable to sudo su
# https://unix.stackexchange.com/questions/202383/how-to-pass-environment-variable-to-sudo-su
create_user:
	@echo "===================== Membuat akun reguler server dan pilihan untuk memberikan hak akses superuser ke akun tersebut ====================="
	$(call install_program, setfacl, acl)
	@read -p "Username? " username; \
		read -p "Is superuser? [y/n] " is_superuser; \
		read -p "Is deployer? [y/n] " is_deployer; \
		if [ $$username ]; then \
			sudo adduser $$username; \
			if [ $${is_superuser:-n} = y ]; then \
				sudo usermod -aG sudo $$username; \
				rsync --archive --chown=$$username:$$username ~/.ssh /home/$$username; \
			else \
				sudo setfacl -R -m u:$$username:rwx /home/$$username/; \
			fi; \
			sudo usermod -aG docker $$username; \
			if [ $${is_deployer:-n} = y ]; then \
				echo "$$username ALL=(ALL:ALL) NOPASSWD: ALL" | sudo EDITOR='tee -a' visudo; \
				read -p "Email? " email; \
				if [ $$email ]; then \
					echo "===================== Buat SSH Keygen dan kosongkan password SSH saat pembuatan! =====================" \
					&& su - $$username -c "ssh-keygen -t rsa -C $$email -b 4096" \
					&& su - $$username -c 'cat ~/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys' \
					&& echo "===================== Salin isi dari private key ke repositori GitLab =====================" \
					&& echo "===================== bagian Settings > CI/CD > Variables =====================" \
					&& echo "===================== Beri nama varibale SSH_PRIVATE_KEY, jangan pilih Protected State! =====================" \
					&& echo "===================== Tambahkan variable USERNAME_DEPLOYER dan masukkan username yang telah dibuat ke dalamnya. =====================" \
					&& echo "===================== Tambahkan juga variable SSH_HOST dan masukkan Host Server ke dalamnya. =====================" \
					&& su - $$username -c 'cat ~/.ssh/id_rsa' \
					&& echo "===================== Salin isi dari public key ke repositori GitLab =====================" \
					&& echo "===================== bagian Settings > CI/CD > Deploy Keys =====================" \
					&& echo "===================== Isi title dengan USERNAME_DEPLOYER@SSH_HOST =====================" \
					&& echo "===================== Langkah ini diperlukan, karena repositori yang dipergunakan mode private. =====================" \
					&& su - $$username -c 'cat ~/.ssh/id_rsa.pub'; \
				fi; \
			fi; \
			echo "Create $$username is done!"; \
		fi

create_superuser:
	@echo "===================== Membuat akun superuser server ====================="
	$(call install_program, setfacl, acl)
	@read -p "Username? " username; \
		if [ $$username ]; then \
			sudo adduser $$username; \
			sudo usermod -aG sudo $$username; \
			rsync --archive --chown=$$username:$$username ~/.ssh /home/$$username; \
			sudo usermod -aG docker $$username; \
			echo "Create $$username is done!"; \
		fi

create_deployer:
	@echo "===================== Membuat akun deployer server untuk GitLab CI/CD ====================="
	$(call install_program, setfacl, acl)
	@read -p "Username? [deployer] " username; \
		read -p "Email? " email; \
		username=$${username:-deployer}; \
		sudo adduser $$username; \
		sudo usermod -aG docker $$username; \
		sudo setfacl -R -m u:$$username:rwx /home/$$username/; \
		echo "$$username ALL=(ALL:ALL) NOPASSWD: ALL" | sudo EDITOR='tee -a' visudo; \
		if [ $$email ]; then \
			echo "===================== Buat SSH Keygen dan kosongkan password SSH saat pembuatan! =====================" \
			&& su - $$username -c "ssh-keygen -t rsa -C $$email -b 4096" \
			&& su - $$username -c 'cat ~/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys' \
			&& echo "===================== Salin isi dari private key ke GitLab =====================" \
			&& echo "===================== bagian Settings > CI/CD > Variables repositori =====================" \
			&& echo "===================== Beri nama varibale SSH_PRIVATE_KEY, jangan pilih Protected State! =====================" \
			&& echo "===================== Tambahkan variable USERNAME_DEPLOYER dan masukkan username yang telah dibuat ke dalamnya. =====================" \
			&& echo "===================== Tambahkan juga variable SSH_HOST dan masukkan Host Server ke dalamnya. =====================" \
			&& su - $$username -c 'cat ~/.ssh/id_rsa' \
			&& echo "===================== Salin isi dari public key ke repositori GitLab =====================" \
			&& echo "===================== bagian Settings > CI/CD > Deploy Keys =====================" \
			&& echo "===================== Isi title dengan USERNAME_DEPLOYER@SSH_HOST =====================" \
			&& echo "===================== Langkah ini diperlukan, karena repositori yang dipergunakan mode private. =====================" \
			&& su - $$username -c 'cat ~/.ssh/id_rsa.pub'; \
		fi; \
		echo "Create $$username is done!"

# How to Set Up SSH Keys on Ubuntu 18.04
# https://linuxize.com/post/how-to-set-up-ssh-keys-on-ubuntu-1804/
deactivate_root:
	@echo "===================== Non-aktifkan login SSH user root dan autentikasi password SSH ====================="
	@sudo cp -f install/sshd_config /etc/ssh/sshd_config
	@sudo systemctl restart sshd

linter_test:
	@echo "===================== Linter Test ====================="
	@cd ../ \
		&& flake8 \
			--exclude env/ \
		&& cd server/

# Permission denied when executing docker commands from Gitlab CI/CD pipeline
# https://stackoverflow.com/questions/51769403/permission-denied-when-executing-docker-commands-from-gitlab-ci-cd-pipeline
register_runner:
	@echo "===================== Register Gitlab Runner ====================="
	@read -p 'Please enter the gitlab-ci coordinator URL: [https://gitlab.com] ' url; \
		read -p 'Please enter the gitlab-ci description for this runner: [app_runner]: ' description; \
		read -p 'Please enter the gitlab-ci token for this runner: ' registration_token; \
		sudo gitlab-runner register -n \
			--url $${url:-'https://gitlab.com/'} \
			--registration-token $$registration_token \
			--executor shell \
			--description $${description:-app_runner} \
			--tag-list live

deploy_pip:
	@echo "===================== Deploy package to pip ====================="
	@env/bin/python setup.py sdist
	@env/bin/twine upload --skip-existing dist/*

deploy_pip_test:
	@echo "===================== Deploy test package to pip ====================="
	@env/bin/python setup.py sdist
	@env/bin/twine upload --skip-existing --repository testpypi dist/*
