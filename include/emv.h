/*
 * This file is part of ccid-utils
 * Copyright (c) 2008 Gianni Tedesco <gianni@scaramanga.co.uk>
 * Released under the terms of the GNU GPL version 3
*/
#ifndef _EMV_H
#define _EMV_H

typedef struct _emv *emv_t;
typedef struct _emv_app *emv_app_t;

/* EMV spec */
_public emv_t emv_init(chipcard_t cc);
_public void emv_fini(emv_t emv);

/* VISA application */
_public int emv_visa_init(emv_t emv);
_public int emv_visa_init_sda(emv_t emv);
_public int emv_visa_pin(emv_t emv, char *pin);

/* LINK application */
_public int emv_link_init(emv_t emv);
_public int emv_link_init_sda(emv_t emv);
_public int emv_link_pin(emv_t emv, char *pin);

#endif /* _EMV_H */
