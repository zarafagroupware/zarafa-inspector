PYQUI := pyuic5
# Support Arch Linux
ifneq (,$(wildcard /etc/arch-release))
	PYQUI := python2-pyuic5
endif

zinspectorlib.py: zarafa-inspector.ui
	$(PYQUI) -o $@  $< 
run:
	$(PYTHON) zinspector.py
