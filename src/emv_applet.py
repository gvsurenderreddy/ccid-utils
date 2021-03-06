import gobject, gtk
import gnome
from gnome import ui
import ccid
import emv

__copyright__ = "Copyright (c) 2009 Gianni Tedesco"
__licence__ = "GPLv3"

visa1152_mod =  "\xA8\x9F\x25\xA5\x6F\xA6\xDA\x25" \
		"\x8C\x8C\xA8\xB4\x04\x27\xD9\x27" \
		"\xB4\xA1\xEB\x4D\x7E\xA3\x26\xBB" \
		"\xB1\x2F\x97\xDE\xD7\x0A\xE5\xE4" \
		"\x48\x0F\xC9\xC5\xE8\xA9\x72\x17" \
		"\x71\x10\xA1\xCC\x31\x8D\x06\xD2" \
		"\xF8\xF5\xC4\x84\x4A\xC5\xFA\x79" \
		"\xA4\xDC\x47\x0B\xB1\x1E\xD6\x35" \
		"\x69\x9C\x17\x08\x1B\x90\xF1\xB9" \
		"\x84\xF1\x2E\x92\xC1\xC5\x29\x27" \
		"\x6D\x8A\xF8\xEC\x7F\x28\x49\x20" \
		"\x97\xD8\xCD\x5B\xEC\xEA\x16\xFE" \
		"\x40\x88\xF6\xCF\xAB\x4A\x1B\x42" \
		"\x32\x8A\x1B\x99\x6F\x92\x78\xB0" \
		"\xB7\xE3\x31\x1C\xA5\xEF\x85\x6C" \
		"\x2F\x88\x84\x74\xB8\x36\x12\xA8" \
		"\x2E\x4E\x00\xD0\xCD\x40\x69\xA6" \
		"\x78\x31\x40\x43\x3D\x50\x72\x5F"
visa1152_exp =  "\x03"

keytbl = {7: (visa1152_mod, visa1152_exp)}

def mod(idx):
	if keytbl.has_key(idx):
		return keytbl[idx][0]
	else:
		print "key index %d not found"%idx
		return None
def exp(idx):
	if keytbl.has_key(idx):
		return keytbl[idx][1]
	else:
		print "key index %d not found"%idx
		return None

class EMVPinDialog(gtk.Dialog):
	def __init__(self, parent, e):
		gtk.Dialog.__init__(self, "EMV Cardholder Verification",
			parent.ccid_util,
			gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
			(gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
			 gtk.STOCK_OK, gtk.RESPONSE_OK))
		self.__emv = e
		c = self.get_content_area()
		c.add(gtk.Label("Enter PIN Number:"))
		self.__entry = gtk.Entry()
		self.__entry.set_visibility(False)
		c.add(self.__entry)
		self.show_all()

	def run(self):
		r = gtk.Dialog.run(self)
		if not r == gtk.RESPONSE_OK:
			return False
		return self.__emv.cvm_pin(self.__entry.get_text())

class EMVDolNumeric:
	def __init__(self, sz):
		self.__sz = sz
		return
	def get_widget(self):
		self.__spin = gtk.SpinButton()
		self.__spin.set_increments(10, 100)
		self.__spin.set_numeric(True)
		self.__spin.set_range(0, 10 ** self.__sz)
		return self.__spin
	def get_data(self):
		val = self.__spin.get_value_as_int()
		data = ""
		while val:
			p1 = val / 10
			r1 = val % 10
			val = val / 10
			p2 = val / 10
			r2 = val % 10
			val = val / 10
			data = "%c"%chr((r2 << 4)|r1) + data
		return data

class EMVDolTVR:
	def __init__(self):
		return
	def __button(self, exp, byte, bit, label):
		b = gtk.CheckButton(label)
		self.__bits[byte][1 << (bit - 1)] = b
		exp.add(b)
	def get_widget(self):
		self.__bits = [{}, {}, {}, {}, {}]
		v = gtk.VBox()
		e = gtk.Expander("Data Authentication")
		v2 = gtk.VBox()
		e.add(v2)
		self.__button(v2, 0, 8, "Offline auth not performed")
		self.__button(v2, 0, 7, "SDA failed")
		self.__button(v2, 0, 6, "ICC data missing")
		self.__button(v2, 0, 5, "Card in terminal exception file")
		self.__button(v2, 0, 4, "DDA failed")
		self.__button(v2, 0, 3, "CDA failed")
		v.add(e)
		e = gtk.Expander("Application Specific")
		v2 = gtk.VBox()
		e.add(v2)
		self.__button(v2, 1, 8, "Version mismatch")
		self.__button(v2, 1, 7, "Expired application")
		self.__button(v2, 1, 6, "Application not yet effective")
		self.__button(v2, 1, 5, "Service not allowed for card product")
		self.__button(v2, 1, 4, "New card")
		v.add(e)
		e = gtk.Expander("Cardholder Verification")
		v2 = gtk.VBox()
		e.add(v2)
		self.__button(v2, 2, 8, "CVM unsuccessful")
		self.__button(v2, 2, 7, "Unrecognized CVM")
		self.__button(v2, 2, 6, "PIN try limit exceeded")
		self.__button(v2, 2, 5, "PIN malfuction")
		self.__button(v2, 2, 4, "PIN not entered")
		self.__button(v2, 2, 3, "Online PIN entered")
		v.add(e)
		e = gtk.Expander("Terminal Risk Management")
		v2 = gtk.VBox()
		e.add(v2)
		self.__button(v2, 3, 8, "Transaction exceeds floor limit")
		self.__button(v2, 3, 7,
			"Lower consecutive offline limit exceeded")
		self.__button(v2, 3, 6,
			"Upper consecutive offline limit exceeded")
		self.__button(v2, 3, 5,
			"Transaction selected randomly for online processing")
		self.__button(v2, 3, 4, "Merchant forced transaction online")
		v.add(e)
		e = gtk.Expander("Terminal Action Analysis")
		v2 = gtk.VBox()
		e.add(v2)
		self.__button(v2, 4, 8, "Default TDOL used")
		self.__button(v2, 4, 7, "Issuer authentication failed")
		self.__button(v2, 4, 6, "Script failed before final AC")
		self.__button(v2, 4, 5, "Script failed after final AC")
		v.add(e)
		return v
	def get_data(self):
		ret = ""
		for i in self.__bits:
			byte = 0
			for (bit, button) in i.items():
				if button.get_active():
					byte = byte | bit
			ret = ret + chr(byte)
		return ret

class EMVDolARC:
	def __init__(self):
		return
	def get_widget(self):
		self.__ls = gtk.ListStore(gobject.TYPE_STRING,
						gobject.TYPE_STRING)
		self.__cb = gtk.ComboBox(self.__ls)
		self.__ls.append(("Offline Approved","Y1"))
		self.__ls.append(("Offline Declined","Z1"))
		self.__ls.append(("Approval (card initiated referral)","Y1"))
		self.__ls.append(("Decline (card initated referral)","Z2"))
		self.__ls.append(("Unable to go online, offline approved","Y3"))
		self.__ls.append(("Unable to go online, offline declined","Z3"))
		cell = gtk.CellRendererText()
		self.__cb.pack_start(cell, True)
		self.__cb.add_attribute(cell, 'text', 0)
		self.__cb.set_active(0)
		return self.__cb
	def get_data(self):
		iter = self.__cb.get_active_iter()
		return self.__ls.get_value(iter, 1)

class EMVDolCountry:
	def __init__(self):
		return
	def get_widget(self):
		self.__ls = gtk.ListStore(gobject.TYPE_STRING,
						gobject.TYPE_STRING)
		self.__cb = gtk.ComboBox(self.__ls)
		self.__ls.append(("United Kingdom","\x08\x26"))
		cell = gtk.CellRendererText()
		self.__cb.pack_start(cell, True)
		self.__cb.add_attribute(cell, 'text', 0)
		self.__cb.set_active(0)
		return self.__cb
	def get_data(self):
		iter = self.__cb.get_active_iter()
		return self.__ls.get_value(iter, 1)

class EMVDolCurrency:
	def __init__(self):
		return
	def get_widget(self):
		self.__ls = gtk.ListStore(gobject.TYPE_STRING)
		self.__cb = gtk.ComboBox(self.__ls)
		self.__ls.append(("Pounds Sterling",))
		cell = gtk.CellRendererText()
		self.__cb.pack_start(cell, True)
		self.__cb.add_attribute(cell, 'text', 0)
		self.__cb.set_active(0)
		return self.__cb
	def get_data(self):
		return ""

class EMVDolDate:
	def __init__(self):
		return
	def __label(self):
		return "%d-%d-%d"%self.__cal.get_date()
	def __day_selected(self, x):
		self.__exp.set_label(self.__label())
	def get_widget(self):
		self.__cal = gtk.Calendar()
		self.__cal.connect("day-selected", self.__day_selected)
		self.__exp = gtk.Expander(self.__label())
		self.__exp.add(self.__cal)
		return self.__exp
	def get_data(self):
		(yy, m, d) = self.__cal.get_date()
		y = yy % 100
		str = chr((y / 10) << 4 | y % 10) + \
			chr((m / 10) << 4 | m % 10) + \
			chr((d / 10) << 4 | d % 10)
		return str

class EMVDolType:
	def __init__(self):
		return
	def get_widget(self):
		return gtk.Label("TODO")
	def get_data(self):
		return ""

class EMVDolRandom:
	def __init__(self):
		return
	def get_widget(self):
		return gtk.Label("TODO")
	def get_data(self):
		return ""

class EMVDolDruidPage(ui.DruidPage):
	def __entry(self, tbl, row, tag):
		if self.__tags.has_key(tag):
			(label, cls, args, vo) = self.__tags[tag]
			obj = cls(*args)
			self.__tags[tag] = (label, cls, args, vo, obj)

			l = gtk.Label(label)
			l.set_alignment(0.9, 0.1)
			tbl.attach(l, 0, 1, row - 1, row, 0, 0)
			tbl.attach(obj.get_widget(), 1, 2, row - 1, row,
					gtk.FILL | gtk.EXPAND, vo)
		else:
			print "unknown DOL tag 0x%.4x"%tag

	def __bcd(self, sz, txt):
		return ''

	def __alnum(self, sz, txt):
		return ''

	def __binary(self, sz, txt):
		return ''

	def __init__(self, cdol):
		ui.DruidPage.__init__(self)
		self.__tags = {
			0x9f02 : ("Amount Authorized",
					EMVDolNumeric, (12,), 0),
			0x9f03 : ("Amount (Other)",
					EMVDolNumeric, (12,), 0),
			0x9f1a : ("Country Code",
					EMVDolCountry, (), 0),
			0x0095 : ("Terminal Verification Results",
					EMVDolTVR, (), gtk.FILL | gtk.EXPAND),
			0x5f2a : ("Currency Code",
					EMVDolCurrency, (), 0),
			0x008a : ("Authorization Response Code",
					EMVDolARC, (), 0),
			0x009a : ("Transaction Date",
					EMVDolDate, (), gtk.FILL | gtk.EXPAND),
			0x009c : ("Transaction Type",
					EMVDolType, (), 0),
			emv.TAG_UNPREDICTABLE_NUMBER:
					("Unpredictable Number",
					EMVDolRandom, (), 0) }
		self.__cdol = cdol

		tbl = gtk.Table(1, 2)
		self.add(tbl)
		row = 1
		for x in emv.dol_read(cdol):
			self.__entry(tbl, row, x)
			row = row + 1
			tbl.resize(row, 2)
	
	def create_dol(self):
		tags = {}
		for (k, v) in self.__tags.items():
			if len(v) < 5:
				continue
			(label, cb, sz, vo, obj) = v
			tags[k] = obj.get_data()
		return emv.dol_create(self.__cdol, tags)

class EMVCryptoDruidPage(ui.DruidPage):
	def __init__(self):
		ui.DruidPage.__init__(self)
		h = gtk.HBox()

		v1 = gtk.VBox()
		v1.add(gtk.Label("Cryptogram Information Data"))
		v1.add(gtk.Label("Application Transaction Counter"))
		v1.add(gtk.Label("Cryptogram"))
		v1.add(gtk.Label("Issuer Application Data"))

		v2 = gtk.VBox()
		self.__cid = gtk.Label()
		self.__atc = gtk.Label()
		self.__cgm = gtk.Label()
		self.__iad = gtk.Label()
		v2.add(self.__cid)
		v2.add(self.__atc)
		v2.add(self.__cgm)
		v2.add(self.__iad)

		h.add(v1)
		h.add(v2)
		self.add(h)

	def cryptogram(self, rx):
		if len(rx) == 3:
			(cid, atc, cgm) = rx
			iad = None
		elif len (rx) == 4:
			(cid, atc, cgm, iad) = rx
		else:
			raise ValueError, "Bad cryptogram format"

		cl = ["AAC", "TC", "ARQC", "AAR"]
		self.__cid.set_label(cl[cid >> 6])
		self.__atc.set_label(str(atc))

		s = ""
		for x in cgm:
			s = s + "%.2x:"%ord(x)
		self.__cgm.set_label(s[:-1])

		if iad:
			s = ""
			for x in iad:
				s = s + "%.2x:"%ord(x)
			self.__iad.set_label(s[:-1])

		return

class EMVActionDialog(gtk.Dialog):
	def __cancel(self, p, d):
		self.response(gtk.RESPONSE_REJECT)

	def __prep(self, p, d):
		d.set_buttons_sensitive(False, True, True, False)

	def __prep_final(self, p, d):
		d.set_buttons_sensitive(False, False, True, False)
		d.set_show_finish(True)

	def __p1_next(self, p, d):
		dol = p.create_dol()
		try:
			rx = self.__emv.generate_ac(emv.AC_ARQC, dol)
		except Exception, e:
			self.__parent.error(e)
			self.response(gtk.RESPONSE_REJECT)
			return
		self.__p2.cryptogram(rx)

	def __p1(self, cdol1):
		p = EMVDolDruidPage(cdol1)
		p.connect("prepare", self.__prep)
		p.connect("next", self.__p1_next)
		p.connect("cancel", self.__cancel)
		return p

	def __p3_next(self, p, d):
		dol = p.create_dol()
		try:
			rx = self.__emv.generate_ac(emv.AC_TC, dol)
		except Exception, e:
			self.__parent.error(e)
			self.response(gtk.RESPONSE_REJECT)
			return
		self.__p4.cryptogram(rx)

	def __p3(self, cdol2):
		p = EMVDolDruidPage(cdol2)
		p.connect("prepare", self.__prep)
		p.connect("next", self.__p3_next)
		p.connect("cancel", self.__cancel)
		self.__cdol2 = cdol2
		return p

	def __p2(self):
		p = EMVCryptoDruidPage()
		p.connect("prepare", self.__prep)
		p.connect("cancel", self.__cancel)
		return p

	def __finish(self, p, d):
		self.response(gtk.RESPONSE_OK)

	def __p4(self):
		p = EMVCryptoDruidPage()
		p.connect("prepare", self.__prep_final)
		p.connect("finish", self.__finish)
		p.connect("cancel", self.__cancel)
		return p

	def __init__(self, parent, e, cdol1, cdol2):
		gtk.Dialog.__init__(self, "EMV Card Action Analysis",
			parent.ccid_util,
			gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
			(gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
			 gtk.STOCK_OK, gtk.RESPONSE_OK))
			
		self.__parent = parent
		self.__emv = e
		self.__d = ui.Druid()
		self.__p1 = self.__p1(cdol1)
		self.__p2 = self.__p2()
		self.__p3 = self.__p3(cdol2)
		self.__p4 = self.__p4()
		self.__d.append_page(self.__p1)
		self.__d.append_page(self.__p2)
		self.__d.append_page(self.__p3)
		self.__d.append_page(self.__p4)

		self.get_content_area().add(self.__d)
		self.show_all()
		self.get_action_area().hide()
		self.set_has_separator(False)

	def run(self):
		if gtk.Dialog.run(self) != gtk.RESPONSE_OK:
			return False
		return True

class EMVAppDialog(gtk.Dialog):
	def __init__(self, parent, e):
		gtk.Dialog.__init__(self, "EMV Application Selection",
			parent.ccid_util,
			gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
			(gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
			 gtk.STOCK_OK, gtk.RESPONSE_OK))
		self.__parent = parent
		self.__emv = e
		c = self.get_content_area()
		self.__options(c)
		self.show_all()

	def __options(self, c):
		self.__rb = []
		rb = None

		try:
			self.__pse_apps = self.__emv.appsel_pse()
		except Exception, e:
			self.__pse_apps = []
			self.__parent.error(e)

		if len(self.__pse_apps):
			c.add(gtk.Label("PSE Applications Supported by Card"))

			rb = None
			for app in self.__pse_apps:
				rb = gtk.RadioButton(rb, app.label())
				rb.emv_app = app
				rb.emv_aid = None
				self.__rb.append(rb)
				c.add(rb)
			c.add(gtk.HSeparator())


		c.add(gtk.Label("Applications Supported by Terminal"))
		for (label,aid) in [
				("VISA DEBIT", "\xa0\x00\x00\x00\x03"),
				("MasterCard", "\xa0\x00\x00\x00\x04"),
				("SWITCH", "\xa0\x00\x00\x00\x05"),
				("American Express", "\xa0\x00\x00\x00\x25"),
				("LINK", "\xa0\x00\x00\x00\x29"),
				("ZKA", "\xa0\x00\x00\x03\x59"),
				("Consorzio BANCOMAT", "\xa0\x00\x00\x01\x41"),
				]:
			rb = gtk.RadioButton(rb, label)
			rb.emv_app = None
			rb.emv_aid = aid
			self.__rb.append(rb)
			c.add(rb)

	def run(self):
		r = gtk.Dialog.run(self)
		if not r == gtk.RESPONSE_OK:
			return False

		sel = None
		for rb in self.__rb:
			if rb.get_active():
				sel = rb
				break
		if sel == None:
			return False

		if sel.emv_app == None:
			self.__emv.select_aid(sel.emv_aid);
		else:
			self.__emv.select_pse(sel.emv_app)

		return True

class EMVShell(gtk.ScrolledWindow):
	def set_status(self, str):
		self.ccid_util.status(str)

	def error(self, e):
		msg = e.args[0]
		if len(e.args) >= 3 and \
				e.args[1] == emv.ERR_EMV and \
				e.args[2] == emv.ERR_BAD_PIN:
			msg = msg + ", %d tries remaining"%\
				self.__emv.pin_try_counter()
		if msg == "":
			msg = "Unknown error"
		self.set_status(msg)
		return

	def __data_tree_init(self):
		i = gtk.Image()

		ts = gtk.TreeStore(gobject.TYPE_STRING, gobject.TYPE_STRING,
				gobject.TYPE_STRING, gobject.TYPE_STRING)

		t = gtk.TreeView(ts)
		t.set_headers_visible(True)
		t.set_headers_clickable(True)
		t.set_enable_search(True)
		t.set_search_column(0)

		r = gtk.CellRendererText()
		i = gtk.CellRendererPixbuf()
		col = gtk.TreeViewColumn("Tag", None)
		col.pack_start(i, True)
		col.add_attribute(i, "stock-id", 0)
		col.pack_start(r, True)
		col.add_attribute(r, "text", 1)
		col.set_resizable(True)
		t.append_column(col)

		r = gtk.CellRendererText()
		col = gtk.TreeViewColumn("Value", r, text = 2)
		col.add_attribute(r, "family", 3)
		col.set_resizable(True)
		t.append_column(col)

		return (ts, t)

	def __add_children(self, iter, d):
		for (k, v) in d.children().items():
			if v.type() == emv.DATA_BINARY:
				t = "Monospace"
			else:
				t = None
			l = v.tag_label()
			if l == None:
				l = "UNKNOWN (0x%x)"%v.tag()
			i = self.__ts.append(iter, (None, l, "%r"%v, t))
			if v.sda():
				self.__sda_recs.append(i)
			self.__data[v.tag()] = v
			self.__add_children(i, v)

	def __read_data(self):
		self.__ts.clear()
		self.__data = {}
		self.__sda_recs = []
		recs = self.__emv.read_app_data()
		for x in recs:
			l = x.tag_label()
			if l == None:
				l = "UNKNOWN (0x%x)"%x.tag()
			i = self.__ts.append(None, (None, l, None, None))
			if x.sda():
				self.__sda_recs.append(i)
			self.__add_children(i, x)

	def __appsel(self, a):
		d = EMVAppDialog(self, self.__emv)
		try:
			ret = d.run()
		except Exception, e:
			self.error(e)
			d.hide()
			return
		d.hide()
		if ret == False:
			return
		try:
			self.__aip = self.__emv.init()
			self.__app = self.__emv.current_app()
			self.set_status("%s selected"%self.__app.label())
			self.__read_data()
			try:
				self.__auc = self.__data[\
					emv.TAG_USAGE_CONTROL].value()
			except KeyError:
				self.__auc = None
		except Exception, e:
			self.error(e)
		return

	def __sda(self):
		try:
			self.__emv.authenticate_static_data(mod, exp)
		except Exception, e:
			self.error(e)
			return
		self.set_status("SDA data authenticated")
		for x in self.__sda_recs:
			self.__ts.set_value(x, 0,
					gtk.STOCK_DIALOG_AUTHENTICATION)
		return

	def __dda(self):
		try:
			self.__emv.authenticate_dynamic(mod, exp)
		except Exception, e:
			self.error(e)
			return
		self.set_status("DDA data authenticated")
		return

	def __auth_card(self, a):
		if self.__aip is None:
			self.set_status("Must select application first")
			return
		if self.__aip[0] & emv.AIP_DDA:
			self.__dda()
		elif self.__aip[0] & emv.AIP_SDA:
			self.__sda()
			return

	def __cvm(self, a):
		d = EMVPinDialog(self, self.__emv)
		try:
			if d.run():
				self.set_status("Cardholder verified")
		except Exception, e:
			self.error(e)
		d.hide()
		return

	def __velocity_check(self, a):
		self.set_status("ATC %d, last online ATC %u"%(
					self.__emv.atc(),
					self.__emv.last_online_atc()))
		return

	def __transact(self, a):
		try:
			cdol1 = self.__data[emv.TAG_CDOL1].value()
			cdol2 = self.__data[emv.TAG_CDOL2].value()
		except KeyError:
			self.set_status("CDOL's not found")
			return

		try:
			d = EMVActionDialog(self, self.__emv,
						cdol1, cdol2)
		except Exception, e:
			self.error(e)
			return
		try:
			ret = d.run()
		except Exception, e:
			self.error(e)
			d.hide()
			return

		d.hide()
		if ret:
			self.set_status("Transaction completed")

	def toolbar(self):
		return [ \
				("Select Application",
					gtk.STOCK_CONNECT,
					self.__appsel),
				("Authenticate Card",
					gtk.STOCK_DIALOG_AUTHENTICATION,
					self.__auth_card),
				("Verify Cardholder",
					gtk.STOCK_YES,
					self.__cvm),
				("Velocity Checking",
					gtk.STOCK_NETWORK,
					self.__velocity_check),
				("Terminal/Card Action Analysis",
					gtk.STOCK_APPLY,
					self.__transact)
			]

	def __init__(self, parent, cci):
		gtk.ScrolledWindow.__init__(self)

		self.ccid_util = parent

		(ts, t) = self.__data_tree_init()
		self.__ts = ts
		self.__sda_recs = []
		self.__data = {}

		self.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
		self.add(t)

		self.__emv = emv.card(cci)
		self.__app = None
		self.__aip = None
		self.__auc = None
