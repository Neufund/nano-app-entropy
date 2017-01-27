// UI to approve or deny the signature proposal
// to be included in main.c
#define TO_HEX(i) (i <= 9 ? '0' + i : 'A' - 10 + i)
#define TO_HEX_IF_NOT_Z(buffer, idx, ny) if (ny > 0) { buffer[idx++] = TO_HEX(ny); }

int uint_to_hex(unsigned int v, char * buffer) {
    // write just 16 bits of path part, no stdio on secure element
    char ny;
    int idx;
    idx = 0;
    ny = ((v & 0xF000) >> 12);
    TO_HEX_IF_NOT_Z(buffer, idx, ny);
    ny = ((v & 0x0F00) >> 8);
    TO_HEX_IF_NOT_Z(buffer, idx, ny);
    ny = ((v & 0x00F0) >> 4);
    TO_HEX_IF_NOT_Z(buffer, idx, ny);
    buffer[idx++] = TO_HEX((v & 0x000F));
    return idx;
}

int bip32_path_buffer_size(unsigned int pathLen) {
    return pathLen*10+1; //char buffer[];
}

void bip32_sprint_path(char * buffer, unsigned int * path, unsigned int pathLen) {
    char *buf = buffer;
    unsigned int ii;
    int idx;
    idx = 0;
    for(ii=0; ii<pathLen; ii++) {
        buf += uint_to_hex(path[ii], buf);
        if (path[ii] & 0x80000000)
            *buf++ = '\'';
        if (ii < pathLen-1)
            *buf++='/';
    }
    *buf = 0x0;
}

// UI displayed when no signature proposal has been received
const bagl_element_t bagl_ui_idle_nanos[] = {
    // type                               userid    x    y   w    h  str rad
    // fill      fg        bg      fid iid  txt   touchparams...       ]
    {{BAGL_RECTANGLE, 0x00, 0, 0, 128, 32, 0, 0, BAGL_FILL, 0x000000, 0xFFFFFF,
      0, 0},
     NULL,
     0,
     0,
     0,
     NULL,
     NULL,
     NULL},

    {{BAGL_LABELINE, 0x02, 0, 12, 128, 11, 0, 0, 0, 0xFFFFFF, 0x000000,
      BAGL_FONT_OPEN_SANS_REGULAR_11px | BAGL_FONT_ALIGNMENT_CENTER, 0},
     "Waiting for path",
     0,
     0,
     0,
     NULL,
     NULL,
     NULL},

    {{BAGL_ICON, 0x00, 3, 12, 7, 7, 0, 0, 0, 0xFFFFFF, 0x000000, 0,
      BAGL_GLYPH_ICON_CROSS},
     NULL,
     0,
     0,
     0,
     NULL,
     NULL,
     NULL},
};

unsigned int bagl_ui_idle_nanos_button(unsigned int button_mask,
                                       unsigned int button_mask_counter) {
    switch (button_mask) {
    case BUTTON_EVT_RELEASED | BUTTON_LEFT:
    case BUTTON_EVT_RELEASED | BUTTON_LEFT | BUTTON_RIGHT:
        io_seproxyhal_touch_exit(NULL);
        break;
    }

    return 0;
}

const bagl_element_t bagl_ui_text_review_nanos[] = {
    // type                               userid    x    y   w    h  str rad
    // fill      fg        bg      fid iid  txt   touchparams...       ]
    {{BAGL_RECTANGLE, 0x00, 0, 0, 128, 32, 0, 0, BAGL_FILL, 0x000000, 0xFFFFFF,
      0, 0},
     NULL,
     0,
     0,
     0,
     NULL,
     NULL,
     NULL},

    {{BAGL_LABELINE, 0x02, 0, 12, 128, 11, 0, 0, 0, 0xFFFFFF, 0x000000,
      BAGL_FONT_OPEN_SANS_EXTRABOLD_11px | BAGL_FONT_ALIGNMENT_CENTER, 0},
     "Verify path",
     0,
     0,
     0,
     NULL,
     NULL,
     NULL},

    {{BAGL_LABELINE, 0x02, 23, 26, 82, 11, 0x80 | 10, 0, 0, 0xFFFFFF, 0x000000,
      BAGL_FONT_OPEN_SANS_REGULAR_11px | BAGL_FONT_ALIGNMENT_CENTER, 26},
     lineBuffer,
     0,
     0,
     0,
     NULL,
     NULL,
     NULL},

    {{BAGL_ICON, 0x00, 3, 12, 7, 7, 0, 0, 0, 0xFFFFFF, 0x000000, 0,
      BAGL_GLYPH_ICON_CROSS},
     NULL,
     0,
     0,
     0,
     NULL,
     NULL,
     NULL},
    {{BAGL_ICON, 0x00, 117, 13, 8, 6, 0, 0, 0, 0xFFFFFF, 0x000000, 0,
      BAGL_GLYPH_ICON_CHECK},
     NULL,
     0,
     0,
     0,
     NULL,
     NULL,
     NULL},
};

// Pick the text elements to display
unsigned char display_text_part(WIDE char * text) {
    unsigned int i;
    if (text[current_text_pos] == '\0') {
        return 0;
    }
    i = 0;
    while ((text[current_text_pos] != 0) && (text[current_text_pos] != '\n') &&
           (i < MAX_CHARS_PER_LINE)) {
        lineBuffer[i++] = text[current_text_pos];
        current_text_pos++;
    }
    if (text[current_text_pos] == '\n') {
        current_text_pos++;
    }
    lineBuffer[i] = '\0';
    return 1;
}

unsigned int
bagl_ui_text_review_nanos_button(unsigned int button_mask,
                                 unsigned int button_mask_counter) {
    switch (button_mask) {
    case BUTTON_EVT_RELEASED | BUTTON_RIGHT:
        io_seproxyhal_touch_approve(NULL);
        /*if (!display_text_part("HUJ")) {
            io_seproxyhal_touch_approve(NULL);
        } else {
            UX_REDISPLAY();
        }*/
        break;

    case BUTTON_EVT_RELEASED | BUTTON_LEFT:
        io_seproxyhal_touch_deny(NULL);
        break;
    }
    return 0;
}

void io_seproxyhal_display(const bagl_element_t *element) {
    io_seproxyhal_display_default((bagl_element_t *)element);
}

void ui_idle(void) {
    uiState = UI_IDLE;
    UX_DISPLAY(bagl_ui_idle_nanos, NULL);
}

void ui_text(void) {
    uiState = UI_TEXT;
    UX_DISPLAY(bagl_ui_text_review_nanos, NULL);
}
