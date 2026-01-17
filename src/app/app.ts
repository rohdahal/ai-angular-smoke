import { Component } from '@angular/core';
import { HomepageComponent } from './homepage/homepage.component';

@Component({
  selector: 'app-root',
  imports: [HomepageComponent],
  templateUrl: './app.html',
  styleUrl: './app.scss'
})
export class App {
}
