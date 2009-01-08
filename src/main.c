/*
 * This file is part of ccid-utils
 * Copyright (c) 2008 Gianni Tedesco <gianni@scaramanga.co.uk>
 * Released under the terms of the GNU GPL version 3
*/

#include <ccid.h>

#include <stdio.h>

static void gsm_select(chipcard_t cc, uint16_t id)
{
	uint8_t buf[] = "\xa0\xa4\x00\x00\x02\xff\xff";
	buf[5] = (id >> 8) & 0xff;
	buf[6] = id & 0xff;
	chipcard_transmit(cc, buf, 7);
}

static void decode_sms(const uint8_t *inp, size_t len)
{
	uint8_t out[len + 1];
	unsigned int i;

	for(i = 0; i <= len; i ++) {
		int ipos = i - i / 8;    int offset = i % 8;

		out[i] = (inp[ipos] & (0x7F >> offset)) << offset;
		if(offset)
			out[i] |= (inp[ipos - 1] & 
					(0x7F << (8 - offset)) & 0xFF)
						>> (8 - offset);
  }

  out[len] = 0;
  printf("-- \"%s\"\n--.--\n", out);
  
}

static void gsm_read_sms(chipcard_t cc, uint8_t rec)
{
	uint8_t buf[] = "\xa0\xb2\xff\x04\xb0";
	const uint8_t *ptr, *end;
	size_t len;

	buf[2] = rec;
	chipcard_transmit(cc, buf, 5);

	ptr = chipcard_rcvbuf(cc, &len);
	if ( ptr == NULL || len == 0 )
		return;
	end = ptr + len;
	
	switch( ptr[0] & 0x7 ) {
	case 0:
		printf("-- Status: free block\n");
		return;
	case 1:
		printf("-- Status: READ\n");
		break;
	case 3:
		printf("-- Status: UNREAD\n");
		break;
	case 5:
		printf("-- Status: SENT\n");
		break;
	case 7:
		printf("-- Status: UNSENT\n");
		break;
	default:
		printf("-- Status: unknown status\n");
		return;
	}

	ptr++;
	printf("- %u bytes SMSC type 0x%.2x\n", ptr[0], ptr[1]);
	ptr += ptr[0] + 1;
	printf("- SMS-DELIVER %u\n", *ptr);
	ptr++;
	printf("- %u byte address type 0x%.2x\n", ptr[0], ptr[1]);
	if ( ptr[1] == 0x91 ) {
		ptr += 8;
	}else{
		ptr += ptr[0] + 1;
	}
	printf("- TP-PID %u\n", *(ptr++));
	printf("- TP-DCS %u\n", *(ptr++));
	ptr += 7;
	printf("- %u septets\n", *ptr);
	ptr++;

	decode_sms(ptr, ptr[-1]);
}

static int found_cci(struct usb_device *dev, int c, int i, int a)
{
	chipcard_t cc;
	cci_t cci;
	int ret = 0;

	cci = cci_probe(dev, c, i, a);
	if ( NULL == cci )
		goto out;
	
	cc = cci_get_slot(cci, 0);
	if ( NULL == cc ) {
		fprintf(stderr, "ccid: error: no slots on CCI\n");
		goto out_close;
	}

	printf("\nWAIT FOR CHIP CARD\n");
	chipcard_wait_for_card(cc);
	printf("\nPOWER ON SLOT\n");
	chipcard_slot_on(cc, CHIPCARD_AUTO_VOLTAGE);
	printf("\nSELECT TELECOM/SMS\n");
	gsm_select(cc, 0x7f10);
	gsm_select(cc, 0x6f3c);
	chipcard_transmit(cc, "\xa0\xc0\x00\x00\x0f", 5); /* GET */
	chipcard_transmit(cc, "\xa0\xb2\x01\x04\xb0", 5);
	for(ret = 0; ret < 0xb; ret++)
		gsm_read_sms(cc, ret);
	//gsm_read_sms(cc, 0x06);
	//gsm_read_sms(cc, 0x07);
	printf("\nPOWER OFF SLOT\n");
	chipcard_slot_off(cc);

	ret = 1;

out_close:
	cci_close(cci);
out:
	return ret;
}

static int check_interface(struct usb_device *dev, int c, int i)
{
	struct usb_interface *iface = &dev->config[c].interface[i];
	int a;

	for (a = 0; a < iface->num_altsetting; a++) {
		struct usb_interface_descriptor *id = &iface->altsetting[a];
		if ( id->bInterfaceClass == 0x0b ) {
			if ( found_cci(dev, c, i, a) )
				continue;
				//return 1;
		}
	}

	return 0;
}

static int check_device(struct usb_device *dev)
{
	int c, i;

	if ( dev->descriptor.idVendor == 0x4e6 &&
		dev->descriptor.idProduct == 0xe003 ) {
		return found_cci(dev, 1, 0, 0);
	}

	for(c = 0; c < dev->descriptor.bNumConfigurations; c++) {
		for(i = 0; i < dev->config[c].bNumInterfaces; i++) {
			if ( check_interface(dev, c, i) )
				return 1;
		}
	}

	return 0;
}

int main(int argc, char **argv)
{
	struct usb_bus *bus, *busses;
	struct usb_device *dev;
	int ret = EXIT_FAILURE;

	usb_init();
	usb_find_busses();
	usb_find_devices();

	busses = usb_get_busses();

	for(bus = busses; bus; bus = bus->next) {
		for(dev = bus->devices; dev; dev = dev->next)
			if ( check_device(dev) )
				ret = EXIT_SUCCESS;
	}

	return ret;
}
