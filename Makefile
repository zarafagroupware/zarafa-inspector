PYQUI := pyuic4
# Support Arch Linux
ifneq (,$(wildcard /etc/arch-release))
	PYQUI := python2-pyuic4
endif

zinspectorlib.py: zarafa-inspector.ui
	$(PYQUI) -o $@  $< 
