@echo off
rmdir /S /Q build
rmdir /S /Q dist
pyinstaller Ebook_Creator.spec
