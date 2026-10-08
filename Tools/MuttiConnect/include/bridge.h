// SPDX-License-Identifier: MPL-2.0
#pragma once
char *MCStart(const char *input, int pair, const char *name);
char *MCStatus(unsigned long long handle);
void MCStop(unsigned long long handle);
void MCFree(char *value);
