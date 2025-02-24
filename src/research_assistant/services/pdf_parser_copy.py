from pdf2docx import Converter
import pdfplumber
import fitz
import os
import json
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Dict, List, Tuple, Generator, Any
import logging
import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ImageMetadata:
    """Data class for storing image metadata"""
    filename: str
    path: str
    extraction_date: str
    page_number: int
    image_index: int
    width: int = None
    height: int = None

class PDFParser:
    def __init__(self, pdf_path: str):
        """
        Initialize parser with PDF file path.
        
        Args:
            pdf_path (str): Path to PDF file
            
        Output: None
        """
        self.pdf_path = pdf_path
        self.pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
        
        # Setup output structure
        self.output_dir = os.path.join('output')
        self.output_text_dir = os.path.join(self.output_dir, 'text', self.pdf_name)
        self.output_tables_dir = os.path.join(self.output_dir, 'tables', self.pdf_name)
        self.output_images_dir = os.path.join(self.output_dir, 'images', self.pdf_name)
        
        # Create output directories
        for dir_path in [self.output_text_dir, self.output_tables_dir, self.output_images_dir]:
            os.makedirs(dir_path, exist_ok=True)
        
        # Initialize result dictionary
        self.result = {
            "metadata": {
                "filename": self.pdf_name,
                "extraction_date": datetime.now().isoformat(),
                "path": pdf_path
            },
            "pages": {},
            "tables": {},
            "images": {}
        }

    def extract_pages(self) -> Generator[Tuple[int, str], None, None]:
        """
        Extract text page by page using generator pattern.
        
        Yields:
            Tuple[int, str]: (page_number, page_text)
            
        Output Structure:
        (1, "Page 1 text...")
        (2, "Page 2 text...")
        """
        cv = Converter(self.pdf_path)
        try:
            for page_num in range(len(cv.fitz_doc)):
                page = cv.fitz_doc[page_num]
                text = page.get_text()
                yield page_num + 1, text
        finally:
            cv.close()

    def extract_text(self) -> Dict[int, str]:
        """
        Extract all text from PDF maintaining page boundaries.
        
        Returns:
            Dict[int, str]: Page numbers mapped to text content
            
        Output Structure:
        {
            1: "Page 1 text...",
            2: "Page 2 text...",
        }
        """
        try:
            pages = {}
            for page_num, text in self.extract_pages():
                if text.strip():
                    pages[page_num] = text.strip()
                    # Save to file
                    output_file = os.path.join(self.output_text_dir, f'page_{page_num}.txt')
                    with open(output_file, 'w', encoding='utf-8') as f:
                        f.write(text.strip())
                    logger.info(f"Extracted text from page {page_num}")
                    
            self.result["pages"] = pages
            return pages
            
        except Exception as e:
            logger.error(f"Error extracting text: {str(e)}")
            raise

    def extract_tables(self) -> Dict[int, List[List[List[str]]]]:
        """
        Extract tables using pdfplumber.
        
        Returns:
            Dict[int, List[List[List[str]]]]: Page numbers mapped to tables
            
        Output Structure:
        {
            1: [
                [["Header1", "Header2"], ["Row1Col1", "Row1Col2"]],
                [["Header1", "Header2"], ["Row1Col1", "Row1Col2"]]
            ],
            2: [...]
        }
        """
        logger.info("Extracting tables")
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, start=1):
                    tables = page.extract_tables()
                    if tables:
                        self.result["tables"][page_num] = tables
                        
                        # Save each table to CSV
                        for table_idx, table in enumerate(tables, start=1):
                            if table and len(table) > 0:  # Check if table has content
                                df = pd.DataFrame(table[1:], columns=table[0])
                                csv_file = os.path.join(
                                    self.output_tables_dir,
                                    f'page_{page_num}_table_{table_idx}.csv'
                                )
                                df.to_csv(csv_file, index=False)
                                logger.info(f"Extracted table {table_idx} from page {page_num}")
            
            return self.result["tables"]
            
        except Exception as e:
            logger.error(f"Error extracting tables: {str(e)}")
            raise

    def extract_images(self) -> Dict[int, List[ImageMetadata]]:
        """
        Extract images using PyMuPDF.
        
        Returns:
            Dict[int, List[ImageMetadata]]: Page numbers mapped to image metadata
            
        Output Structure:
        {
            1: [
                ImageMetadata(filename="page_1_img_1.png", ...),
                ImageMetadata(filename="page_1_img_2.jpg", ...)
            ],
            2: [...]
        }
        """
        logger.info("Extracting images")
        try:
            doc = fitz.open(self.pdf_path)
            for page_num in range(len(doc)):
                page = doc[page_num]
                image_list = page.get_images(full=True)
                
                if len(image_list) > 0:
                    self.result["images"][page_num + 1] = []
                    
                    for img_idx, img in enumerate(image_list, start=1):
                        xref = img[0]
                        base_image = doc.extract_image(xref)
                        
                        # Generate filename and save image
                        image_filename = f"page_{page_num + 1}_image_{img_idx}.{base_image['ext']}"
                        image_path = os.path.join(self.output_images_dir, image_filename)
                        
                        with open(image_path, "wb") as img_file:
                            img_file.write(base_image["image"])
                        
                        # Create and store metadata
                        metadata = ImageMetadata(
                            filename=image_filename,
                            path=image_path,
                            extraction_date=datetime.now().isoformat(),
                            page_number=page_num + 1,
                            image_index=img_idx,
                            width=base_image.get('width'),
                            height=base_image.get('height')
                        )
                        
                        self.result["images"][page_num + 1].append(asdict(metadata))
                        logger.info(f"Extracted image {img_idx} from page {page_num + 1}")
            
            doc.close()
            return self.result["images"]
            
        except Exception as e:
            logger.error(f"Error extracting images: {str(e)}")
            raise

    def save_metadata(self) -> None:
        """
        Save extraction results and metadata to JSON.
        
        Output Structure:
        {
            "metadata": {
                "filename": "example.pdf",
                "extraction_date": "2024-01-16T12:34:56",
                "path": "/path/to/pdf"
            },
            "pages": {1: "text...", 2: "text..."},
            "tables": {1: [...], 2: [...]},
            "images": {1: [{metadata1}, {metadata2}], 2: [...]}
        }
        """
        try:
            metadata_file = os.path.join(self.output_dir, f"{self.pdf_name}_metadata.json")
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.result, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved metadata to {metadata_file}")
        except Exception as e:
            logger.error(f"Error saving metadata: {str(e)}")
            raise

    def parse(self) -> Dict[str, Any]:
        """
        Parse the PDF extracting all content and maintaining page relationships.
        
        Returns:
            Dict[str, Any]: Complete extraction results
            
        Output Structure:
        {
            "metadata": {...},
            "pages": {page_num: text},
            "tables": {page_num: tables},
            "images": {page_num: images}
        }
        """
        logger.info(f"Starting to parse: {self.pdf_path}")
        try:
            self.extract_text()
            self.extract_tables()
            self.extract_images()
            self.save_metadata()
            
            logger.info(f"Successfully parsed: {self.pdf_path}")
            return self.result
        except Exception as e:
            logger.error(f"Error parsing PDF: {str(e)}")
            raise
