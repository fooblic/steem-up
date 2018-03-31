
help:
	@echo 'Makefile for a steem-up deploy                                  '
	@echo '                                                                '
	@echo 'Usage:                                                          '
	@echo '   make      up                ansible synchronize files and run'

up:
	ansible-playbook -v --ask-become-pass ./steem-up.ansible.yml

.PHONY: up help