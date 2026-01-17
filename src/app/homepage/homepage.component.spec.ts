import { ComponentFixture, TestBed } from '@angular/core/testing';
import { HomepageComponent } from './homepage.component';

describe('HomepageComponent', () => {
  let component: HomepageComponent;
  let fixture: ComponentFixture<HomepageComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [HomepageComponent]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(HomepageComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should have navLinks with correct length', () => {
    expect(component.navLinks.length).toBe(5);
  });

  it('should have categories with correct length', () => {
    expect(component.categories.length).toBe(5);
  });

  it('should have products with correct length', () => {
    expect(component.products.length).toBe(6);
  });

  it('should have collections with correct length', () => {
    expect(component.collections.length).toBe(2);
  });

  it('should have perks with correct length', () => {
    expect(component.perks.length).toBe(3);
  });

  it('should have testimonials with correct length', () => {
    expect(component.testimonials.length).toBe(3);
  });

  it('isDiscounted should return true for products with original price greater than current price', () => {
    const product = { ...component.products[0], originalPrice: 150 };
    expect(component.isDiscounted(product)).toBeTrue();
  });

  it('isDiscounted should return false for products without original price or original price less than or equal to current price', () => {
    const product = { ...component.products[0], originalPrice: undefined };
    expect(component.isDiscounted(product)).toBeFalse();

    const product2 = { ...component.products[0], originalPrice: 128 };
    expect(component.isDiscounted(product2)).toBeFalse();
  });
});
