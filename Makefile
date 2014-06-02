PYQUI := pyuic4
ifeq ($(which pyqui4),)
	PYQUI := python2-pyuic4
endif

zinspectorlib.py: zarafa-inspector.ui
	$(PYQUI) -o $@  $< 
