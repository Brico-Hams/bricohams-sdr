// Arduino.h mínimo para compilar en el PC la lógica del firmware (KISS, digipeater, APRS)
// y probarla con tests/test_rak_aprs.py. No forma parte del firmware.
#pragma once
#include <string>
#include <cstring>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cmath>
#include <cctype>

class String {
public:
    std::string s;
    String() {}
    String(const char* c) : s(c ? c : "") {}
    String(const std::string& x) : s(x) {}
    String(char c) : s(1, c) {}
    String(int v) : s(std::to_string(v)) {}
    String(long v) : s(std::to_string(v)) {}
    String(unsigned v) : s(std::to_string(v)) {}
    String(unsigned long v) : s(std::to_string(v)) {}
    String(double v, int dec) { char b[64]; snprintf(b, sizeof b, "%.*f", dec, v); s = b; }
    String(float v, int dec) { char b[64]; snprintf(b, sizeof b, "%.*f", dec, (double)v); s = b; }
    unsigned length() const { return s.size(); }
    const char* c_str() const { return s.c_str(); }
    char charAt(unsigned i) const { return i < s.size() ? s[i] : 0; }
    char operator[](unsigned i) const { return charAt(i); }
    void setCharAt(unsigned i, char c) { if (i < s.size()) s[i] = c; }
    int indexOf(char c, unsigned from = 0) const { auto p = s.find(c, from); return p == std::string::npos ? -1 : (int)p; }
    int indexOf(const String& x, unsigned from = 0) const { auto p = s.find(x.s, from); return p == std::string::npos ? -1 : (int)p; }
    int indexOf(const char* x, unsigned from = 0) const { return indexOf(String(x), from); }
    String substring(unsigned a) const { return a >= s.size() ? String("") : String(s.substr(a)); }
    String substring(unsigned a, unsigned b) const { if (b > s.size()) b = s.size(); if (a >= b) return String(""); return String(s.substr(a, b - a)); }
    bool startsWith(const String& x) const { return s.compare(0, x.s.size(), x.s) == 0 && s.size() >= x.s.size(); }
    bool endsWith(const String& x) const { return s.size() >= x.s.size() && s.compare(s.size() - x.s.size(), x.s.size(), x.s) == 0; }
    long toInt() const { return atol(s.c_str()); }
    void toUpperCase() { for (auto& c : s) c = toupper(c); }
    void reserve(unsigned n) { s.reserve(n); }
    String& operator+=(const String& x) { s += x.s; return *this; }
    String& operator+=(const char* x) { s += x; return *this; }
    String& operator+=(char c) { s += c; return *this; }
    String& operator+=(int v) { s += std::to_string(v); return *this; }
    bool operator==(const String& x) const { return s == x.s; }
    bool operator==(const char* x) const { return s == x; }
    bool operator!=(const String& x) const { return s != x.s; }
    bool operator!=(const char* x) const { return s != x; }
};
inline String operator+(const String& a, const String& b) { return String(a.s + b.s); }
inline String operator+(const String& a, const char* b) { return String(a.s + b); }
inline String operator+(const char* a, const String& b) { return String(std::string(a) + b.s); }
inline String operator+(const String& a, char b) { return String(a.s + b); }

inline bool isDigit(char c) { return isdigit((unsigned char)c); }
inline bool isAlpha(char c) { return isalpha((unsigned char)c); }
inline bool isAlphaNumeric(char c) { return isalnum((unsigned char)c); }
inline bool isUpperCase(char c) { return isupper((unsigned char)c); }
inline long random(long a, long b) { return a + rand() % (b - a); }
extern unsigned long fake_millis;
inline unsigned long millis() { return fake_millis; }
#define HIGH 1
#define LOW 0
#define F(x) (x)
#define constrain(a, l, h) ((a) < (l) ? (l) : ((a) > (h) ? (h) : (a)))
using std::isnan;
#ifndef NAN
#define NAN (0.0/0.0)
#endif
