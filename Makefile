PYQUI := pyuic4
PYTHON := python
# Support Arch Linux
ifneq (,$(wildcard /etc/arch-release))
	PYQUI := python2-pyuic4
	PYTHON := python2
endif

zinspectorlib.py: zarafa-inspector.ui
	$(PYQUI) -o $@  $< 
run:
	$(PYTHON) zinspector.py
