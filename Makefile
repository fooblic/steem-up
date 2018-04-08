
help:
	@echo 'Makefile for a steem-up deploy                                  '
	@echo '                                                                '
	@echo 'Usage:                                                          '
	@echo '   make      up                ansible synchronize '
	@echo '   make      follow            ansible synchronize files and run'

up:
	ansible-playbook -v ./steem-up.ansible.yml
	
follow:
	ansible-playbook -v --ask-become-pass ./steem-follow.ansible.yml

.PHONY: up help