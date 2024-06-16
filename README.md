

# EoneReader

**EoneReader** is a sophisticated and user-friendly eBook reader application designed for quick and efficient eBook handling. It allows users to upload, read, and listen to eBooks in a variety of formats. The application provides a seamless reading experience with features like multi-color text display, image handling, TTS audio listening, search, bookmarking, night mode, and a clean Table of Contents (TOC) for easy navigation.

## Features

- **Quick and Fast Upload**: Easily upload your eBooks and get started in no time.
- **Multicolor Source Text Display**: Enjoy eBooks with rich and vibrant text formatting.
- **Image Handling**: View images embedded in your eBooks as intended by the author.
- **Text-to-Speech (TTS) Audio Listening**: Listen to your eBooks with integrated TTS functionality.
- **Search Feature**: Quickly find specific text or phrases within your eBook.
- **Bookmarking**: Save your place in the book and return to it with ease.
- **Night Mode**: Reduce eye strain by switching to night mode for reading in low-light environments.
- **Neat and Clean TOC**: Navigate through your eBook with a well-organized Table of Contents.
- **Next and Previous Navigation**: Move between sections and pages with simple next and previous buttons.
- **Simple Upload-to-Read Interface**: A straightforward interface that makes reading your eBooks as easy as uploading and starting to read.

## Installation/Instructions for Use

1. **Install EoneReader.exe**: Download and install the EoneReader executable file.
2. **Run as Administrator**: To ensure full functionality, right-click on the EoneReader.exe file and select "Run as Administrator".
3. **Open the Interface**: Upon running the application, the index interface will appear.
4. **Select an eBook/ePub File**: Choose a valid eBook or ePub file from your device.
5. **Upload the File**: Click the "Upload to Read" button to upload your selected file.
6. **View the Reader Interface**: The read_epub interface will open with two panels.
7. **Book Browsing List**: The left-side panel contains the "Book Browsing List".
8. **Enjoy Reading and Listening**: Click on any item in the browsing list to start reading. Use the integrated text-to-speech (TTS) feature to listen to the content if you prefer.
9. **Explore Features**: Read the overhead title bar to discover and enjoy all available features, such as multi-color text display, image rendering, TTS audio listening, search, bookmarking, night mode, neat and clean table of contents, and navigation options.
10. **Cross-Platform Availability**: The EoneReader is available for all platforms.

### Important Notes
- Ensure you have a valid eBook or ePub document for the best experience.
- The features available depend on the contents of the source document.
- EoneReader is free to test for 14 days without any data limit.

## Usage

1. **Running the Application**
    ```bash
    dist/EoneReader/EoneReader.exe
    ```

2. **Accessing the Interface**
    Open your web browser and go to `http://127.0.0.1:5000/index`.

3. **Uploading an eBook**
    - Click on the "Upload" button.
    - Select your `.epub` file and upload it.

4. **Reading an eBook**
    - Navigate through the Table of Contents to select chapters.
    - Use the next and previous buttons to move between sections.
    - Toggle night mode for a better reading experience in the dark.
    - Use the search feature to find specific content.
    - Bookmark your favorite sections.

## Project Structure

- `EoneReader.py`: Main application file.
- `templates/`: Directory containing HTML templates.
  - `index.html`: Main interface template.
  - `read_epub.html`: eBook reading template.
- `static/`: Directory containing static files like CSS and JavaScript.
- `uploads/`: Directory where uploaded eBooks are stored.
- `unzipped_books/`: Directory where extracted eBook content is stored.
- `requirements.txt`: List of dependencies.
- `EoneReader.spec`: PyInstaller specification file for building the executable.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contact

For any inquiries or issues, please contact [rdsaini@mail.com](mailto:rdsaini@mail.com).

---

Enjoy your reading experience with **EoneReader**! Your feedback at [rdsaini@mail.com](mailto:rdsaini@mail.com) is welcome to motivate us for further features/improvement. 

All rights are reserved with Rameshwar Dass Saini for "Vareshwar & Humisha Hisar 125001. India.
